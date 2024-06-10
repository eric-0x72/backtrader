#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt


class SmaCross(bt.SignalStrategy):
    params = dict(sma1=50, sma2=200)
    total_profit = 0

    def notify_order(self, order):
        if not order.alive():
            print('{} {} {}@{}'.format(
                bt.num2date(order.executed.dt),
                'buy' if order.isbuy() else 'sell',
                order.executed.size,
                order.executed.price)
            )

    def notify_trade(self, trade):
        if trade.isclosed:
            print('profit {}'.format(trade.pnlcomm))
            self.total_profit += trade.pnlcomm
            print('total profit {}'.format(self.total_profit))

    def next(self):
        if self.crossover > 0:
            if not self.position:
                self.buy(size=10)
        else:
            if self.sma1[0] > self.sma2[0]:  # Check if fast SMA is greater than slow SMA
                # Check for local maxima and downtrend condition
                if self.local_maxima is None or self.sma1[0] > self.local_maxima:
                    self.local_maxima = self.sma1[0]
                    self.flag = False

                else:
                    # 预判会死叉,提前close
                    if self.diff <= 2.5 and self.diff > 0 and not self.flag:
                        # print(">>> date: {}".format(bt.num2date(self.data.datetime[0])), self.diff[0])
                        self.flag = True
                        self.close()

                    # 逃顶策略
                    if self.diff >= 6.0:
                        self.close()
            # else:
            #     # 止损
            #     if self.sma1[0] - self.sma2[0] > 2 and self.position:
            #         print(">>> 触发止损!!!")
            #         # self.close()

    # def next(self):  # simple golden/death cross  ***
    #     if self.crossover > 0:  # Golden Cross
    #         if not self.position:
    #             self.buy(size=10)
    #     elif self.crossover < 0:  # Dead Cross
    #         if self.position:
    #             self.close()

    def __init__(self):
        self.sma1 = bt.ind.SMA(period=self.params.sma1)
        self.sma2 = bt.ind.SMA(period=self.params.sma2)
        self.crossover = bt.ind.CrossOver(self.sma1, self.sma2)
        self.diff = self.sma1 - self.sma2
        # self.signal_add(bt.SIGNAL_LONG, self.diff)  #
        self.local_maxima = None
        self.flag = None


def runstrat(pargs=None):
    args = parse_args(pargs)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(args.cash)

    data0 = bt.feeds.YahooFinanceData(
        dataname=args.data,
        fromdate=datetime.datetime.strptime(args.fromdate, '%Y-%m-%d'),
        todate=datetime.datetime.strptime(args.todate, '%Y-%m-%d'))
    cerebro.adddata(data0)

    cerebro.addstrategy(SmaCross, **(eval('dict(' + args.strat + ')')))
    cerebro.addsizer(bt.sizers.FixedSize, stake=args.stake)

    cerebro.run()
    if args.plot:
        cerebro.plot(**(eval('dict(' + args.plot + ')')))
    cerebro.plot()


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='sigsmacross')

    parser.add_argument('--data', required=False,
                        default='../../datas/yhoo-1996-2015.txt',
                        # default='../../datas/nvda-1999-2014.txt',
                        # default='../../datas/orcl-1995-2014.txt',
                        help='Yahoo Ticker')

    # for testing purpose, nvda-1999-2014
    # parser.add_argument('--fromdate', required=False, default='2005-10-31', help='Ending date in YYYY-MM-DD format')
    # parser.add_argument('--todate', required=False, default='2007-06-05', help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--fromdate', required=False, default='1996-10-31', help='Ending date in YYYY-MM-DD format')
    parser.add_argument('--todate', required=False, default='2015-06-05', help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash', required=False, action='store', type=float,
                        default=10000, help=('Starting cash'))

    parser.add_argument('--stake', required=False, action='store', type=int,
                        default=10, help=('Stake to apply'))

    parser.add_argument('--strat', required=False, action='store', default='',
                        help=('Arguments for the strategy'))

    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const='{}',
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example:\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
