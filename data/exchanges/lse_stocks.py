"""
London Stock Exchange (LSE) listed stocks.
"""

from ..models import Stock

LSE_STOCKS = {
    # UK Large Cap
    "SHEL.L": Stock("SHEL.L", "Shell plc", "LSE", "UK", "Energy", "Oil & Gas", "large", "GBP", "British multinational oil and gas company"),
    "AZN.L": Stock("AZN.L", "AstraZeneca PLC", "LSE", "UK", "Healthcare", "Pharmaceuticals", "large", "GBP", "British-Swedish multinational pharmaceutical company"),
    "ULVR.L": Stock("ULVR.L", "Unilever PLC", "LSE", "UK", "Consumer Staples", "Personal Care", "large", "GBP", "British multinational consumer goods company"),
    "HSBA.L": Stock("HSBA.L", "HSBC Holdings plc", "LSE", "UK", "Financials", "Banking", "large", "GBP", "British multinational investment bank and financial services holding company"),
    "BP.L": Stock("BP.L", "BP p.l.c.", "LSE", "UK", "Energy", "Oil & Gas", "large", "GBP", "British multinational oil and gas company"),
    "LLOY.L": Stock("LLOY.L", "Lloyds Banking Group plc", "LSE", "UK", "Financials", "Banking", "large", "GBP", "British financial services group"),
    "BARC.L": Stock("BARC.L", "Barclays PLC", "LSE", "UK", "Financials", "Banking", "large", "GBP", "British multinational investment bank and financial services company"),
    "GSK.L": Stock("GSK.L", "GSK plc", "LSE", "UK", "Healthcare", "Pharmaceuticals", "large", "GBP", "British multinational pharmaceutical and biotechnology company"),
    "VOD.L": Stock("VOD.L", "Vodafone Group Plc", "LSE", "UK", "Communication Services", "Telecommunications", "large", "GBP", "British multinational telecommunications company"),
    "BT-A.L": Stock("BT-A.L", "BT Group plc", "LSE", "UK", "Communication Services", "Telecommunications", "large", "GBP", "British multinational telecommunications holding company"),
    "TSCO.L": Stock("TSCO.L", "Tesco PLC", "LSE", "UK", "Consumer Staples", "Retail", "large", "GBP", "British multinational groceries and general merchandise retailer"),
    "RIO.L": Stock("RIO.L", "Rio Tinto Group", "LSE", "UK", "Materials", "Mining", "large", "GBP", "British-Australian multinational metals and mining corporation"),
    "GLEN.L": Stock("GLEN.L", "Glencore plc", "LSE", "UK", "Materials", "Mining", "large", "GBP", "British multinational commodity trading and mining company"),
    "LSEG.L": Stock("LSEG.L", "London Stock Exchange Group plc", "LSE", "UK", "Financials", "Financial Markets", "large", "GBP", "British financial markets infrastructure business"),
    "RDSB.L": Stock("RDSB.L", "Royal Dutch Shell plc", "LSE", "UK", "Energy", "Oil & Gas", "large", "GBP", "British-Dutch multinational oil and gas company"),
}
