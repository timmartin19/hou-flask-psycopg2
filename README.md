# Highly Opinionated Utils: Flask-Psycopg2

Provides the ability to integrate Flask directly with psycopg2
No need for a filthy ORM

## Installation

```bash
pip install hou-flask-pscyopg2
```

Sometimes on macs psycopg2 is a little pain in the ass.  You'll see
errors like 

```bash
>>> ld: library not found for -lssl
>>> clang: error: linker command failed with exit code 1 (use -v to see invocation)
>>> error: command 'clang' failed with exit status 1
```

To fix these try any of the following

1. `xcode-select --install`
2. `brew install openssl`
3. `LDFLAGS="-L/usr/local/opt/openssl/lib" CPPFLAGS="-I/usr/local/opt/openssl/include" pip install hou-flask-pscyopg2`
