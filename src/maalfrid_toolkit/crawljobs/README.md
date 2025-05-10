# Crawljob configurations
Place config files for crawljobs in this folder. maalfrid_toolkit is based on focused crawls of a limited set of domains. The format is YAML with the following fields:

```yaml
jobid: 1 # your internal identifier for the job
domain: example.com # the domain you want to restrict the crawl job to
crawler: wget # the crawler to use (wget or browsertrix)
seed: https://example.com # the seed to start from
span_hosts: true # include sub-domains?
crawl_depth: 12 # the depth of the crawl within the domain
enabled: true # only execute job if true
timeout_seconds: 1209600 # job will be stopped after the timeout
exclude_paths: # list of paths to exclude
- /mytestpath
exclude_subdomains: # list of subdomains to exclude
- mytestdomain.example.com
exclude_urls: # list of URL (regexes) to exclude
- /my-url?my-parameter=my-value
use_sitemap: false # use sitemap, not implemented in wget
ignore_robotstxt: false # whether to respect robots.txt (you should)
```
