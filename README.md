# local-broadcast

A python library to send message to all instances of the current running program on local LAN

https://pypi.org/project/local-broadcast/

## WIP

Work in progress, not ready for use yet.

## install

```
pip3 install local_broadcast@git+https://github.com/gambuzzi/local-broadcast
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