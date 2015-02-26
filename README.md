# redis-statsd

redis-statsd is a small, dependency free Python program for periodically fetching stats via Redis' INFO
command and emitting them to a local StatsD.

# Motivation

At [Keen](http://keen.io) we run some Redis instances in Mesos with dynamically allocated ports. We use Datadog and
therefore have an on-box StatsD instance to report to. Therefore this little program can be started with a dynamic
port and report metrics out to DogStatsD!

# Optional DogStatsD Tag Support

The `--no-tags` option will disable support for [DogStatsD](http://docs.datadoghq.com/guides/dogstatsd/)-style tags.

# Usage

```
usage: redis-statsd.py [-h] [--period PERIOD] [--prefix PREFIX]
                       [--redis-host REDIS_HOST] [--redis-port REDIS_PORT]
                       [--statsd-host STATSD_HOST] [--statsd-port STATSD_PORT]
                       [--no-tags]

Collect metrics from Redis and emit to StatsD

optional arguments:
  -h, --help            show this help message and exit
  --period PERIOD       The period at which to collect and emit metrics
  --prefix PREFIX       The prefix to use for metric names
  --redis-host REDIS_HOST
                        The address of the Redis host to connect to
  --redis-port REDIS_PORT
                        The port of the Redis host to connect to
  --statsd-host STATSD_HOST
                        The port of the StatsD host to connect to
  --statsd-port STATSD_PORT
                        The port of the Redis port to connect to
  --no-tags             Disable tags for use with DogStatsD
```