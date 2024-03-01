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

#Reading tiprank from local crawling pipeline
#Need to update github action to merge gurufocus daily with weekly tiprank
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
SmartScore = pn.widgets.EditableRangeSlider(name='SmartScore', start=0, end=10, value=(9, 10), step=1)
Industry = pn.widgets.CheckBoxGroup( name='Select Industry', value=list(set(DFmerge_tipranks_gurufocus.Industry)), options=list(set(DFmerge_tipranks_gurufocus.Industry)), inline=True)
Sector = pn.widgets.CheckBoxGroup( name='Select Sector', value=list(set(DFmerge_tipranks_gurufocus.Sector)), options=list(set(DFmerge_tipranks_gurufocus.Sector)), inline=False)
GFValuepercent = pn.widgets.FloatSlider(name='GFValuepercent', start=-100, end=1000, step=1, value=30.0)

cash_icon = """
<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-cash" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
  <path d="M7 9m0 2a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2z" />
  <path d="M14 14m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" />
  <path d="M17 9v-2a2 2 0 0 0 -2 -2h-10a2 2 0 0 0 -2 2v6a2 2 0 0 0 2 2h2" />
</svg>
"""
download_button = pn.widgets.FileDownload(icon=cash_icon, button_type='success', icon_size='2em', file='watchlist.txt', label="Download Watchlist", filename="watchlist.txt", callback=get_table_download_link)

def export_watchlist(df):
    return df['Ticker'].str.cat(sep=', ')

def get_table_download_link(df):
    import base64
    b64 = base64.b64encode(export_watchlist(df).encode()).decode()
    today = str(datetime.datetime.today().year) + '-' + str('{:02d}'.format(
        datetime.datetime.today().month)) + '-' + str('{:02d}'.format(datetime.datetime.today().day))
    href = f'<a href="data:file/txt;base64,{b64}" download="watchlist.txt">Download ! </a>'
    return href


def get_DF(DF,ticker,SmartScore,GFValuepercent ,Sector):
  DF.to_csv('watchlist.txt')
  if ticker and ticker!="ALL":
    return pn.widgets.Tabulator(DF.query("Ticker == @ticker"), name='DataFrame' , height=800, widths=200 ,)
  else:
    return pn.widgets.Tabulator( DF.query("SmartScore>=@SmartScore[0] & SmartScore <= @SmartScore[1] & GFValuepercent>=@GFValuepercent & Sector in @ Sector" ), name='DataFrame' , height=800, widths=200 ,)


pn.extension('tabulator')
bound_plot = pn.bind(get_DF, DF=DFmerge_tipranks_gurufocus,ticker=ticker,SmartScore=SmartScore,GFValuepercent=GFValuepercent ,Sector=Sector)

pn.Column(pn.Row(pn.Column(ticker,SmartScore,GFValuepercent ,Sector),bound_plot),download_button).servable(title="Fair Value Ranking - Merged Gurufocus & Tiprank")