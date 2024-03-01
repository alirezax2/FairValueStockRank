import pandas as pd
import numpy as np
import os
from datetime import datetime

import hvplot as hv
import holoviews as hvs
import panel as pn
import hvplot.pandas

pn.extension('bokeh', template='bootstrap')

#Rading gurufocus from github action pipeline
current_datetime = datetime.now().strftime("%Y-%m-%d")    
daily_gurufocus_csvfile = f"https://raw.githubusercontent.com/alirezax2/GurusFocusCrawl/main/gurufocus/GuruFocus_merged_{current_datetime}.csv"
daily_gurufocus_DF = pd.read_csv(daily_gurufocus_csvfile)

#Reading tiprank from local crawling pipeline; Need to update github action to merge gurufocus daily with weekly tiprank
monthly_tiprank_csvfile = f"https://raw.githubusercontent.com/alirezax2/GurusFocusCrawl/main/tipranks/tipranks_2024-02-28.csv"
monthly_tiprank_DF = pd.read_csv(monthly_tiprank_csvfile)

#Merging tipranks with Gurufocus
DFgurufocus = daily_gurufocus_DF[['Ticker' , 'GFValue']] # , 'GFValuediff']]
DFmerge_tipranks_gurufocus = DFgurufocus.merge(monthly_tiprank_DF)

if 'Price' in DFmerge_tipranks_gurufocus.columns and 'GFValue' in DFmerge_tipranks_gurufocus.columns:
  DFmerge_tipranks_gurufocus['GFValuepercent'] = 100* ( DFmerge_tipranks_gurufocus['GFValue'] - DFmerge_tipranks_gurufocus['Price']) / DFmerge_tipranks_gurufocus['Price']
  DFmerge_tipranks_gurufocus['GFValuepercent'] = DFmerge_tipranks_gurufocus['GFValuepercent'].round(2)
  DFmerge_tipranks_gurufocus['Market Capitalization'] = DFmerge_tipranks_gurufocus['Market Capitalization'] / 1e9
  DFmerge_tipranks_gurufocus['MarketCap'] = DFmerge_tipranks_gurufocus['Market Capitalization'].round(1)
  DFmerge_tipranks_gurufocus = DFmerge_tipranks_gurufocus.drop(columns=['Market Capitalization'])

#widget
ticker = pn.widgets.AutocompleteInput(name='Ticker', options=list(DFmerge_tipranks_gurufocus.Ticker) , placeholder='Write Ticker here همین جا',value='ALL', restrict=False)
SmartScore = pn.widgets.EditableRangeSlider(name='Smart Score', start=0, end=10, value=(9, 10), step=1)
Industry = pn.widgets.CheckBoxGroup( name='Select Industry', value=list(set(DFmerge_tipranks_gurufocus.Industry)), options=list(set(DFmerge_tipranks_gurufocus.Industry)), inline=True)
Sector = pn.widgets.CheckBoxGroup( name='Select Sector', value=list(set(DFmerge_tipranks_gurufocus.Sector)), options=list(set(DFmerge_tipranks_gurufocus.Sector)), inline=False)
GFValuepercent = pn.widgets.FloatSlider(name='GF Value %', start=-100, end=1000, step=1, value=30.0)
MarketCap = pn.widgets.FloatSlider(name='Market Capital (B$)', start=0, end=4000, step=1, value=1)

def get_DF(DF,ticker,SmartScore,GFValuepercent ,Sector,MarketCap):
  if ticker and ticker!="ALL":
    return pn.widgets.Tabulator(DF.query("Ticker == @ticker"), height=800, widths=200 ,)
  else:
    return pn.widgets.Tabulator( DF.query("SmartScore>=@SmartScore[0] & SmartScore <= @SmartScore[1] & GFValuepercent>=@GFValuepercent & Sector in @ Sector & MarketCap>@MarketCap"), height=800, widths=200 ,)

pn.extension('tabulator')
bound_plot = pn.bind(get_DF, DF=DFmerge_tipranks_gurufocus,ticker=ticker,SmartScore=SmartScore,GFValuepercent=GFValuepercent ,Sector=Sector ,MarketCap=MarketCap)

pn.Column(pn.Row(pn.Column(ticker,SmartScore,GFValuepercent ,MarketCap, Sector),bound_plot)).servable(title="Fair Value Ranking - Merged Gurufocus & Tiprank")