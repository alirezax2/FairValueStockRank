import pandas as pd
import numpy as np
import os
from datetime import datetime

import hvplot as hv
import holoviews as hvs
import panel as pn
import hvplot.pandas as pd

pn.extension('bokeh', template='bootstrap')


def _extract_raw_data(ticker="MSFT", period="6mo", interval="1d"):
  import yfinance as yf
  df = yf.Ticker(ticker)
  return df.history(period=period, interval=interval).reset_index()

def _transform_data(raw_data: pd.DataFrame):
  from datetime import timedelta
  data = raw_data[["Date", "Open", "High", "Low", "Close", "Volume"]].copy(deep=True).rename(columns={
      "Date": "time",
      "Open": "open",
      "High": "high",
      "Low": "low",
      "Close": "close",
      "Volume": "volume",
  })
  t_delta = timedelta(hours=1)
  data['time_start'] = data.time - 9*t_delta # rectangles start
  data['time_end'] = data.time + 9*t_delta    # rectangles end
  data['positive'] = ((data.close - data.open)>0).astype(int)
  return data

def make_candle_stick(ticker):
    raw_data = _extract_raw_data(ticker = ticker)
    data = _transform_data(raw_data=raw_data)
    _delta = np.median(np.diff(data.time))
    candlestick = hv.Segments(data, kdims=['time', 'low', 'time', 'high']) * hv.Rectangles(data, kdims=['time_start','open', 'time_end', 'close'], vdims=['positive'])
    candlestick = candlestick.redim.label(Low='Values')
    candlechart = pn.Column(candlestick.opts(hv.opts.Rectangles(color='positive', cmap=['red', 'green'], responsive=True), hv.opts.Segments(color='black', height=400, responsive=True , show_grid=True)) , 
                     data.hvplot(x="time", y="volume", kind="line", responsive=True, height=200).opts( show_grid=True) )
                    #  data.hvplot(y="volume", kind="bar", responsive=True, height=200) )
    return candlechart

#Rading gurufocus from github action pipeline
current_datetime = datetime.now().strftime("%Y-%m-%d")    
daily_gurufocus_csvfile = f"https://raw.githubusercontent.com/alirezax2/GurusFocusCrawl/main/gurufocus/GuruFocus_merged_{current_datetime}.csv"
daily_gurufocus_DF = pd.read_csv(daily_gurufocus_csvfile)

#Reading tiprank from local crawling pipeline; Need to update github action to merge gurufocus daily with weekly tiprank
monthly_tiprank_csvfile = f"https://raw.githubusercontent.com/alirezax2/GurusFocusCrawl/main/tipranks/tipranks_2024-02-28.csv"
monthly_tiprank_DF = pd.read_csv(monthly_tiprank_csvfile)[['Ticker','SmartScore','Market Capitalization','Sector','Industry']]

#Reading finviz from github action pipeline another repository(public)
daily_finviz_csvfile = f"https://raw.githubusercontent.com/alirezax2/FinVizCrawl/main/finviz/FinViz_{current_datetime}.csv"
daily_finviz_DF = pd.read_csv(daily_finviz_csvfile)
daily_finviz_DF['FinVizPrice']  = pd.to_numeric(daily_finviz_DF['Price'], errors='coerce').fillna(0).astype(float)
daily_finviz_DF['FinVizTarget']  = pd.to_numeric(daily_finviz_DF['Target Price'], errors='coerce').fillna(0).astype(float)
daily_finviz_DF['FinVizTargetpercent'] = (100*(daily_finviz_DF['FinVizTarget']-daily_finviz_DF['FinVizPrice'])/daily_finviz_DF['FinVizPrice']).round(2)
daily_finviz_DF = daily_finviz_DF[['Ticker','Price','FinVizTarget','FinVizTargetpercent']]


#Merging tipranks with Gurufocus
DFgurufocus = daily_gurufocus_DF[['Ticker' , 'GFValue']] # , 'GFValuediff']]
DFmerge_tipranks_gurufocus = DFgurufocus.merge(monthly_tiprank_DF)

#Merging Finviz with Merged last one
DFmerge_tipranks_gurufocus = DFmerge_tipranks_gurufocus.merge(daily_finviz_DF)

if 'Price' in DFmerge_tipranks_gurufocus.columns and 'GFValue' in DFmerge_tipranks_gurufocus.columns:
  DFmerge_tipranks_gurufocus['GFValuepercent'] = 100* ( DFmerge_tipranks_gurufocus['GFValue'] - DFmerge_tipranks_gurufocus['Price']) / DFmerge_tipranks_gurufocus['Price']
  DFmerge_tipranks_gurufocus['GFValuepercent'] = DFmerge_tipranks_gurufocus['GFValuepercent'].round(2)
  DFmerge_tipranks_gurufocus['Market Capitalization'] = DFmerge_tipranks_gurufocus['Market Capitalization'] / 1e9
  DFmerge_tipranks_gurufocus['MarketCap'] = DFmerge_tipranks_gurufocus['Market Capitalization'].round(1)
  DFmerge_tipranks_gurufocus = DFmerge_tipranks_gurufocus.drop(columns=['Market Capitalization'])
  DFmerge_tipranks_gurufocus = DFmerge_tipranks_gurufocus[['Ticker', 'Sector', 'Industry' , 'MarketCap' , 'SmartScore', 'Price' , 'GFValue' , 'GFValuepercent' , 'FinVizTarget','FinVizTargetpercent']]

#widget
ticker = pn.widgets.AutocompleteInput(name='Ticker', options=list(DFmerge_tipranks_gurufocus.Ticker) , placeholder='Write Ticker here همین جا',value='ALL', restrict=False)
SmartScore = pn.widgets.EditableRangeSlider(name='Smart Score', start=0, end=10, value=(9, 10), step=1)
Industry = pn.widgets.CheckBoxGroup( name='Select Industry', value=list(set(DFmerge_tipranks_gurufocus.Industry)), options=list(set(DFmerge_tipranks_gurufocus.Industry)), inline=True)
Sector = pn.widgets.CheckBoxGroup( name='Select Sector', value=list(set(DFmerge_tipranks_gurufocus.Sector)), options=list(set(DFmerge_tipranks_gurufocus.Sector)), inline=False)
GFValuepercent = pn.widgets.FloatSlider(name='GF Value %', start=-100, end=1000, step=1, value=30.0)
FinVizTargetpercent = pn.widgets.FloatSlider(name='FinViz Target %', start=-100, end=1000, step=1, value=30.0)
MarketCap = pn.widgets.FloatSlider(name='Market Capital (B$)', start=0, end=4000, step=1, value=1)

def get_DF(DF,ticker,SmartScore,GFValuepercent, FinVizTargetpercent, Sector,MarketCap):
  if ticker and ticker!="ALL":
    table1 = pn.widgets.Tabulator(DF.query("Ticker == @ticker"), height=800, widths=200, show_index=False)
    chart1 = make_candle_stick(ticker)
    return pn.Column(table1,chart1)
  else:
    return pn.widgets.Tabulator( DF.query("SmartScore>=@SmartScore[0] & SmartScore <= @SmartScore[1] & GFValuepercent>=@GFValuepercent & FinVizTargetpercent>@FinVizTargetpercent & Sector in @Sector & MarketCap>@MarketCap"), height=800, widths=200, show_index=False)

pn.extension('tabulator')
bound_plot = pn.bind(get_DF, DF=DFmerge_tipranks_gurufocus,ticker=ticker,SmartScore=SmartScore,GFValuepercent=GFValuepercent, FinVizTargetpercent=FinVizTargetpercent, Sector=Sector ,MarketCap=MarketCap)

pn.Column(pn.Row(pn.Column(ticker,SmartScore,GFValuepercent, FinVizTargetpercent, MarketCap, Sector),bound_plot)).servable(title="Fair Value Ranking - Merged Gurufocus & Tiprank")