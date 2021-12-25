======================
bitfinex-python-client
======================

Python package to communicate with the bitfinex.net API.

Compatible with Python 2.7+ and Python 3.3+


Overview
========

There are two classes. One for the public part of API and a second for the
trading part.

Public class doesn't need user credentials, because API commands which this
class implements are not bound to bitfinex user account.

Description of API: https://www.bitfinex.com/pages/api


Install
=======

Install from git::

    pip install git+git://github.com/streblo/bitfinex-python-client.git


Usage
=====

Here's a quick example of usage::

    >>> import bitfinex.client

    >>> public_client = bitfinex.client.Public()
    >>> print(public_client.ticker()['last_trade'])
    620.23

    >>> trading_client = bitfinex.client.Trading(key='xxx', secret='xxx')
    >>> print(trading_client.new_order(amount=10.0, price=610.00))
    <order_id>




How to activate a new API key
=============================

Get the API key from the website: https://www.bitfinex.com/account/api
