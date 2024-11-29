# local-broadcast

A python library to send message to all instances of the current running program on local LAN

https://pypi.org/project/local-broadcast/

## WIP

Work in progress, not ready for use yet.

## install

```
pip3 install local_broadcast@git+https://github.com/gambuzzi/local-broadcast
```

## dev mode install

```
python -m pip install -e .
```

## example

```
python3 src/example/chat_async.py
```

## build package

```
python3 -m pip install --upgrade build
python3 -m build
python3 -m pip install --upgrade twine
python3 -m twine upload dist/*
```

## to create a new release in github and on pypi

- update version in pyproject.toml
- run (changing the version number)
```
git tag -a "0.0.7" -m "0.0.7"
git push --tags
```