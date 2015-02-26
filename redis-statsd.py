#!/usr/bin/env python

import argparse
import socket
import sys
import time

parser = argparse.ArgumentParser(description='Collect metrics from Redis and emit to StatsD')
parser.add_argument('--period', dest='period', type=int, default=20, help='The period at which to collect and emit metrics')
parser.add_argument('--prefix', dest='prefix', type=str, default='redis', help='The prefix to use for metric names')
parser.add_argument('--redis-host', dest='redis_host', type=str, default='localhost', help='The address of the Redis host to connect to')
parser.add_argument('--redis-port', dest='redis_port', type=int, default=6379, help='The port of the Redis host to connect to')
parser.add_argument('--statsd-host', dest='statsd_host', type=str, default='localhost', help='The port of the StatsD host to connect to')
parser.add_argument('--statsd-port', dest='statsd_port', type=int, default=8125, help='The port of the Redis port to connect to')
parser.add_argument('--no-tags', dest='tags', action='store_false', help='Disable tags for use with DogStatsD')

args = parser.parse_args()

GAUGES = {
    'blocked_clients': 'blocked_clients',
    'connected_clients': 'connected_clients',
    'mem_fragmentation_ratio': 'mem_fragmentation_ratio',
    'uptime_in_seconds': 'uptime_in_seconds',
    'used_memory': 'used_memory',
    'used_memory_lua': 'used_memory_lua',
    'used_memory_peak': 'used_memory_peak',
    'used_memory_rss': 'used_memory_rss'
}
COUNTERS = {
    'evicted_keys': 'evicted_keys',
    'expired_keys': 'expired_keys',
    'instantaneous_ops_per_sec': 'instantaneous_ops_per_sec',
    'keyspace_hits': 'keyspace_hits',
    'keyspace_misses': 'keyspace_misses',
    'latest_fork_usec': 'latest_fork_usec',
    'migrate_cached_sockets': 'migrate_cached_sockets',
    'pubsub_channels': 'pubsub_channels',
    'pubsub_patterns': 'pubsub_patterns',
    'rejected_connections': 'rejected_connections',
    'sync_full': 'sync_full',
    'sync_partial_err': 'sync_partial_err',
    'sync_partial_ok': 'sync_partial_ok',
    'total_commands_processed': 'total_commands_processed',
    'total_connections_received': 'total_connections_received'
}
KEYSPACE_COUNTERS = {
    'expires': 'expires',
    'keys': 'keys'
}
KEYSPACE_GAUGES = {
    'avg_ttl': 'avg_ttl'
}

last_seens = {}

def send_metric(name, mtype, value, tags=None):
    tagstring = ''
    finalvalue = value
    if tags is not None and args.tags:
        tagstring = '#{}'.format(','.join(tags))
    if mtype == 'c':
        # For counters we will calculate our own deltas.
        mkey = '{}:{}'.format(name, tagstring)
        if mkey in last_seens:
            # global finalvalue
            # calculate our deltas and don't go below 0
            finalvalue = max(0, value - last_seens[mkey])
        else:
            # We'll default to 0, since we don't want our first counter
            # to be some huge number.
            finalvalue = 0
        last_seens[mkey] = value

    met = '{}:{}|{}{}'.format(name, finalvalue, mtype, tagstring)
    out_sock.sendto(met, (args.statsd_host, args.statsd_port))

def linesplit(socket):
    buffer = socket.recv(4096)
    buffering = True
    while buffering:
        if "\n" in buffer:
            (line, buffer) = buffer.split("\n", 1)
            if(line == "\r"):
                buffering = False
            yield line
        else:
            more = socket.recv(4096)
            if not more:
                buffering = False
            else:
                buffer += more
    if buffer:
        yield buffer

while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.redis_host, args.redis_port))
    s.send("INFO\n")

    stats = {}
    stats['keyspaces'] = {}

    for line in linesplit(s):
        if '# Clients' in line:
            for l in line.split("\n"):
                if ':keys' in l:
                    (keyspace, kstats) = l.split(':')
                    if keyspace not in stats['keyspaces']:
                        stats['keyspaces'][keyspace] = {}
                    for ks in kstats.split(','):
                        (n, v) = ks.split('=')
                        stats['keyspaces'][keyspace][n] = v.rstrip()

                elif ':' in l:
                    (name, value) = l.split(':')
                    stats[name] = value.rstrip()

    s.close()

    out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for g in GAUGES:
        if g in stats:
            send_metric('{}.{}'.format(args.prefix, g), 'g', float(stats[g]))

    for c in COUNTERS:
        if c in stats:
            send_metric('{}.{}'.format(args.prefix, c), 'c', float(stats[c]))

    for ks in stats['keyspaces']:
        for kc in KEYSPACE_COUNTERS:
            if kc in stats['keyspaces'][ks]:
                send_metric('{}.keyspace.{}'.format(
                    args.prefix, kc), 'c',
                float(stats['keyspaces'][ks][kc]), ['keyspace={}'.format(ks)]
                )

        for kg in KEYSPACE_GAUGES:
            if kg in stats['keyspaces'][ks]:
                send_metric('{}.keyspace.{}'.format(
                    args.prefix, kg), 'g',
                    float(stats['keyspaces'][ks][kg]), ['keyspace={}'.format(ks)]
                )

    out_sock.close()
    time.sleep(10)

