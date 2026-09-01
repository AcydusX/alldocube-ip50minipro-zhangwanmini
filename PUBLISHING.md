# Publishing / repository identity

Canonical GitHub repository:

```text
AcydusX/alldocube-ip50minipro-zhangwanmini
```

The repository intentionally excludes firmware images and private signing material.

Clone with SSH:

```bash
git clone git@github.com:AcydusX/alldocube-ip50minipro-zhangwanmini.git
```

HTTPS:

```bash
git clone https://github.com/AcydusX/alldocube-ip50minipro-zhangwanmini.git
```

Before publishing future local changes, verify that no private key or firmware binary has been staged:

```bash
git status --short
git ls-files | grep -E '\.(pem|key|img|bin|raw|sparse)$' && {
  echo 'STOP: sensitive/large binary unexpectedly tracked'
  exit 1
} || true
```

The canonical external binary identities are in `manifests/known-good-sha256.txt` and `manifests/artifacts.yaml`.
