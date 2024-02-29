import pandas as pd
import numpy as np
import os
from datetime import datetime

import hvplot as hv
import holoviews as hvs
import panel as pn
import hvplot.pandas

pn.extension('bokeh', template='bootstrap')


#Need to update github action to merge gurufocus daily with weekly tiprank

current_datetime = datetime.now().strftime("%Y-%m-%d")    
daily_gurufocus_csvfile = f"https://raw.githubusercontent.com/alirezax2/GurusFocusCrawl/main/gurufocus/GuruFocus_merged_{current_datetime}.csv"

daily_gurufocus_DF = pd.read_csv(daily_gurufocus_csvfile)


monthly_tiprank_csvfile = f"https://raw.githubusercontent.com/alirezax2/GurusFocusCrawl/main/tipranks/tipranks_2024-02-28.csv"

monthly_tiprank_DF = pd.read_csv(monthly_tiprank_csvfile)

#Merging with Gurufocus
DFgurufocus = daily_gurufocus_DF[['Ticker' , 'GFValue']] # , 'GFValuediff']]
DFmerge_tipranks_gurufocus = DFgurufocus.merge(monthly_tiprank_DF)

if 'Price' in DFmerge_tipranks_gurufocus.columns and 'GFValue' in DFmerge_tipranks_gurufocus.columns:
  DFmerge_tipranks_gurufocus['GFValuepercent'] = 100* ( DFmerge_tipranks_gurufocus['GFValue'] - DFmerge_tipranks_gurufocus['Price']) / DFmerge_tipranks_gurufocus['Price']


ticker = pn.widgets.AutocompleteInput(name='Ticker', options=list(DFmerge_tipranks_gurufocus.Ticker) , placeholder='Write Ticker here همین جا',value='ALL', restrict=False)
# ticker.value = "AAPL"

SmartScore = pn.widgets.EditableRangeSlider(name='SmartScore', start=0, end=10, value=(9, 10), step=1)

Industry = pn.widgets.CheckBoxGroup( name='Select Industry', value=list(set(DFmerge_tipranks_gurufocus.Industry)), options=list(set(DFmerge_tipranks_gurufocus.Industry)), inline=True)
Sector = pn.widgets.CheckBoxGroup( name='Select Sector', value=list(set(DFmerge_tipranks_gurufocus.Sector)), options=list(set(DFmerge_tipranks_gurufocus.Sector)), inline=False)
GFValuepercent = pn.widgets.FloatSlider(name='GFValuepercent', start=-100, end=1000, step=1, value=30.0)
alert = pn.pane.Alert(f'{DFmerge_tipranks_gurufocus.shape} ', alert_type="success")
# SmartScore = pn.widgets.IntSlider(name='SmartScore', start=0, end=10, step=1, value=9)
# Sector = pn.widgets.Select(name='Sector', value='Mean', options=list(DFmerge_tipranks_gurufocus.Sector))
# Industry = pn.widgets.Select(name='Sector', value='Mean', options=list(DFmerge_tipranks_gurufocus.Sector))


def get_DF(DF,ticker,SmartScore,GFValuepercent ,Sector):
  if ticker and ticker!="ALL":
    return pn.widgets.Tabulator(DF.query("Ticker == @ticker"), name='DataFrame' , height=500, widths=200 ,)
  else:
    return pn.widgets.Tabulator( DF.query("SmartScore>=@SmartScore[0] & SmartScore <= @SmartScore[1] & GFValuepercent>=@GFValuepercent & Sector in @ Sector" ), name='DataFrame' , height=500, widths=200 ,)

def get_alert(DF,ticker,SmartScore,GFValuepercent ,Sector):
  if ticker:
    DF2 = DF.query("Ticker == @ticker")
  else:
    DF2 = DF
  DF = DF.query("SmartScore>=@SmartScore[0] & SmartScore <= @SmartScore[1]")
  return pn.pane.Alert(f'{DF.shape} ', alert_type="success")

pn.extension('tabulator')
bound_plot = pn.bind(get_DF, DF=DFmerge_tipranks_gurufocus,ticker=ticker,SmartScore=SmartScore,GFValuepercent=GFValuepercent ,Sector=Sector)

pn.Column(pn.Row(pn.Column(ticker,SmartScore,GFValuepercent ,Sector),bound_plot)).servable(title="Fair Value Ranking - Gurufocus & Tiprank")