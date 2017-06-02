from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Order

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    balance = cb.get_balance()
    if balance is not None:
        bids, asks = cb.get_order_book()
        if len(bids) > 0:
            top_bid = bids[0]
            my_bid = Order()
            my_bid.price = round(top_bid.price - (top_bid.price * 0.005), 2)  # less 5%
            if balance.gbp_available > 10:
                my_bid.amount = round(10.0 / my_bid.price, 4)
                print('top_bid: {} my_bid: {}'.format(top_bid, my_bid))

                buy = my_bid.asmap()
                buy['ttl'] = 60
                order, resp_json = cb.place_limit_order('buy', buy)
                if order is not None:
                    print(order)
                else:
                    print('no buy: {}'.format(resp_json))

        if len(asks) > 0:
            top_ask = asks[0]
            my_ask = Order()
            my_ask.price = round(top_ask.price + (top_ask.price * 0.005), 2)  # +5%

            my_ask.amount = round(10.0 / my_ask.price, 4)
            if my_ask.amount < balance.xbt_available:
                print('top_ask: {} my_ask: {}'.format(top_ask, my_ask))
                sell = my_ask.asmap()
                sell['ttl'] = 60
                order, resp_json = cb.place_limit_order('sell', sell)
                if order is not None:
                    print(order)
                else:
                    print('no sell: {}'.format(resp_json))
