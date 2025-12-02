"""
Bombay Stock Exchange (BSE) stocks.
Major Indian companies across all sectors.
"""

from ..models import Stock

# Bombay Stock Exchange stocks
BSE_STOCKS = {
    # India - Technology (Large Cap)
    "TCS.BO": Stock("TCS.BO", "Tata Consultancy Services Limited", "BSE", "India", "Technology", "IT Services", "mega", "INR", "World's largest IT services company by market cap"),
    "INFY.BO": Stock("INFY.BO", "Infosys Limited", "BSE", "India", "Technology", "IT Services", "large", "INR", "Global leader in next-generation digital services and consulting"),
    "WIPRO.BO": Stock("WIPRO.BO", "Wipro Limited", "BSE", "India", "Technology", "IT Services", "large", "INR", "Leading global information technology services company"),
    "HCLTECH.BO": Stock("HCLTECH.BO", "HCL Technologies Limited", "BSE", "India", "Technology", "IT Services", "large", "INR", "Global technology company focused on digital transformation"),
    "TECHM.BO": Stock("TECHM.BO", "Tech Mahindra Limited", "BSE", "India", "Technology", "IT Services", "large", "INR", "Digital transformation and business re-engineering services"),
    "LTI.BO": Stock("LTI.BO", "Larsen & Toubro Infotech Limited", "BSE", "India", "Technology", "IT Services", "large", "INR", "Global technology consulting and digital solutions company"),
    "MINDTREE.BO": Stock("MINDTREE.BO", "Mindtree Limited", "BSE", "India", "Technology", "IT Services", "large", "INR", "Digital transformation and technology services company"),
    
    # India - Banking/Finance (Large Cap)
    "RELIANCE.BO": Stock("RELIANCE.BO", "Reliance Industries Limited", "BSE", "India", "Energy", "Oil & Gas", "mega", "INR", "India's largest private sector company and conglomerate"),
    "HDFCBANK.BO": Stock("HDFCBANK.BO", "HDFC Bank Limited", "BSE", "India", "Financials", "Banking", "mega", "INR", "India's largest private sector bank by assets"),
    "ICICIBANK.BO": Stock("ICICIBANK.BO", "ICICI Bank Limited", "BSE", "India", "Financials", "Banking", "large", "INR", "India's second-largest private sector bank"),
    "SBIN.BO": Stock("SBIN.BO", "State Bank of India", "BSE", "India", "Financials", "Banking", "large", "INR", "India's largest public sector bank"),
    "KOTAKBANK.BO": Stock("KOTAKBANK.BO", "Kotak Mahindra Bank Limited", "BSE", "India", "Financials", "Banking", "large", "INR", "Leading Indian private sector bank"),
    "AXISBANK.BO": Stock("AXISBANK.BO", "Axis Bank Limited", "BSE", "India", "Financials", "Banking", "large", "INR", "India's third-largest private sector bank"),
    "INDUSINDBK.BO": Stock("INDUSINDBK.BO", "IndusInd Bank Limited", "BSE", "India", "Financials", "Banking", "large", "INR", "Leading new generation private sector bank"),
    "BAJFINANCE.BO": Stock("BAJFINANCE.BO", "Bajaj Finance Limited", "BSE", "India", "Financials", "Financial Services", "large", "INR", "Leading non-banking financial company"),
    "HDFCLIFE.BO": Stock("HDFCLIFE.BO", "HDFC Life Insurance Company Limited", "BSE", "India", "Financials", "Insurance", "large", "INR", "Leading life insurance company"),
    "SBILIFE.BO": Stock("SBILIFE.BO", "SBI Life Insurance Company Limited", "BSE", "India", "Financials", "Insurance", "large", "INR", "Leading life insurance company"),
    
    # India - Consumer Staples (Large Cap)
    "HINDUNILVR.BO": Stock("HINDUNILVR.BO", "Hindustan Unilever Limited", "BSE", "India", "Consumer Staples", "Personal Care", "large", "INR", "India's largest FMCG company"),
    "ITC.BO": Stock("ITC.BO", "ITC Limited", "BSE", "India", "Consumer Staples", "Tobacco", "large", "INR", "Diversified conglomerate with cigarettes, hotels, and FMCG"),
    "NESTLEIND.BO": Stock("NESTLEIND.BO", "Nestle India Limited", "BSE", "India", "Consumer Staples", "Food Products", "large", "INR", "Leading food and beverage company"),
    "BRITANNIA.BO": Stock("BRITANNIA.BO", "Britannia Industries Limited", "BSE", "India", "Consumer Staples", "Food Products", "large", "INR", "Leading biscuit and dairy products company"),
    "DABUR.BO": Stock("DABUR.BO", "Dabur India Limited", "BSE", "India", "Consumer Staples", "Personal Care", "large", "INR", "Leading Ayurvedic and natural healthcare company"),
    "GODREJCP.BO": Stock("GODREJCP.BO", "Godrej Consumer Products Limited", "BSE", "India", "Consumer Staples", "Personal Care", "large", "INR", "Leading consumer goods company"),
    "MARICO.BO": Stock("MARICO.BO", "Marico Limited", "BSE", "India", "Consumer Staples", "Personal Care", "large", "INR", "Leading consumer products company"),
    
    # India - Healthcare/Pharmaceuticals (Large Cap)
    "SUNPHARMA.BO": Stock("SUNPHARMA.BO", "Sun Pharmaceutical Industries Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "large", "INR", "India's largest pharmaceutical company"),
    "DRREDDY.BO": Stock("DRREDDY.BO", "Dr. Reddy's Laboratories Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "large", "INR", "Leading pharmaceutical and biotechnology company"),
    "CIPLA.BO": Stock("CIPLA.BO", "Cipla Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "large", "INR", "Global pharmaceutical company focused on respiratory care"),
    "DIVISLAB.BO": Stock("DIVISLAB.BO", "Divi's Laboratories Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "large", "INR", "Leading pharmaceutical ingredients and intermediates company"),
    "BIOCON.BO": Stock("BIOCON.BO", "Biocon Limited", "BSE", "India", "Healthcare", "Biotechnology", "large", "INR", "Leading biopharmaceutical company"),
    "LUPIN.BO": Stock("LUPIN.BO", "Lupin Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "large", "INR", "Global pharmaceutical company"),
    "APOLLOHOSP.BO": Stock("APOLLOHOSP.BO", "Apollo Hospitals Enterprise Limited", "BSE", "India", "Healthcare", "Healthcare Services", "large", "INR", "Leading healthcare services provider"),
    
    # India - Automotive (Large Cap)
    "MARUTI.BO": Stock("MARUTI.BO", "Maruti Suzuki India Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "India's largest passenger car manufacturer"),
    "TATAMOTORS.BO": Stock("TATAMOTORS.BO", "Tata Motors Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "Leading automotive manufacturer with global presence"),
    "M&M.BO": Stock("M&M.BO", "Mahindra & Mahindra Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "Leading SUV and tractor manufacturer"),
    "BAJAJ-AUTO.BO": Stock("BAJAJ-AUTO.BO", "Bajaj Auto Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "Leading two-wheeler and three-wheeler manufacturer"),
    "HEROMOTOCO.BO": Stock("HEROMOTOCO.BO", "Hero MotoCorp Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "World's largest two-wheeler manufacturer"),
    "EICHERMOT.BO": Stock("EICHERMOT.BO", "Eicher Motors Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "Manufacturer of Royal Enfield motorcycles"),
    "ASHOKLEY.BO": Stock("ASHOKLEY.BO", "Ashok Leyland Limited", "BSE", "India", "Consumer Discretionary", "Automotive", "large", "INR", "Leading commercial vehicle manufacturer"),
    
    # India - Materials/Metals (Large Cap)
    "TATASTEEL.BO": Stock("TATASTEEL.BO", "Tata Steel Limited", "BSE", "India", "Materials", "Steel", "large", "INR", "India's largest private sector steel company"),
    "HINDALCO.BO": Stock("HINDALCO.BO", "Hindalco Industries Limited", "BSE", "India", "Materials", "Aluminum", "large", "INR", "Leading aluminum and copper producer"),
    "JSWSTEEL.BO": Stock("JSWSTEEL.BO", "JSW Steel Limited", "BSE", "India", "Materials", "Steel", "large", "INR", "Leading integrated steel producer"),
    "SAIL.BO": Stock("SAIL.BO", "Steel Authority of India Limited", "BSE", "India", "Materials", "Steel", "large", "INR", "India's largest steel producer"),
    "COALINDIA.BO": Stock("COALINDIA.BO", "Coal India Limited", "BSE", "India", "Materials", "Mining", "large", "INR", "World's largest coal mining company"),
    "VEDL.BO": Stock("VEDL.BO", "Vedanta Limited", "BSE", "India", "Materials", "Mining", "large", "INR", "Diversified natural resources company"),
    "HINDZINC.BO": Stock("HINDZINC.BO", "Hindustan Zinc Limited", "BSE", "India", "Materials", "Mining", "large", "INR", "World's second-largest zinc producer"),
    
    # India - Energy (Large Cap)
    "ONGC.BO": Stock("ONGC.BO", "Oil and Natural Gas Corporation Limited", "BSE", "India", "Energy", "Oil & Gas", "large", "INR", "India's largest oil and gas exploration company"),
    "IOC.BO": Stock("IOC.BO", "Indian Oil Corporation Limited", "BSE", "India", "Energy", "Oil & Gas", "large", "INR", "India's largest commercial oil company"),
    "BPCL.BO": Stock("BPCL.BO", "Bharat Petroleum Corporation Limited", "BSE", "India", "Energy", "Oil & Gas", "large", "INR", "Leading oil refining and marketing company"),
    "HINDPETRO.BO": Stock("HINDPETRO.BO", "Hindustan Petroleum Corporation Limited", "BSE", "India", "Energy", "Oil & Gas", "large", "INR", "Major oil refining company"),
    "GAIL.BO": Stock("GAIL.BO", "GAIL (India) Limited", "BSE", "India", "Energy", "Oil & Gas", "large", "INR", "India's largest natural gas company"),
    "NTPC.BO": Stock("NTPC.BO", "NTPC Limited", "BSE", "India", "Energy", "Electric Utilities", "large", "INR", "India's largest power generation company"),
    "POWERGRID.BO": Stock("POWERGRID.BO", "Power Grid Corporation of India Limited", "BSE", "India", "Energy", "Electric Utilities", "large", "INR", "India's largest power transmission company"),
    
    # India - Telecommunications (Large Cap)
    "BHARTIARTL.BO": Stock("BHARTIARTL.BO", "Bharti Airtel Limited", "BSE", "India", "Communication Services", "Telecommunications", "large", "INR", "Leading telecommunications services provider"),
    "JIO.BO": Stock("JIO.BO", "Reliance Jio Infocomm Limited", "BSE", "India", "Communication Services", "Telecommunications", "large", "INR", "India's largest telecom operator"),
    
    # India - Infrastructure/Construction (Large Cap)
    "LT.BO": Stock("LT.BO", "Larsen & Toubro Limited", "BSE", "India", "Industrials", "Construction & Engineering", "large", "INR", "Leading engineering and construction conglomerate"),
    "ULTRACEMCO.BO": Stock("ULTRACEMCO.BO", "UltraTech Cement Limited", "BSE", "India", "Materials", "Construction Materials", "large", "INR", "India's largest cement company"),
    "ADANIPORTS.BO": Stock("ADANIPORTS.BO", "Adani Ports and Special Economic Zone Limited", "BSE", "India", "Industrials", "Transportation Infrastructure", "large", "INR", "India's largest private ports operator"),
    "ADANIENT.BO": Stock("ADANIENT.BO", "Adani Enterprises Limited", "BSE", "India", "Industrials", "Conglomerates", "large", "INR", "Flagship company of Adani Group"),
    
    # India - Consumer Discretionary (Large Cap)
    "TITAN.BO": Stock("TITAN.BO", "Titan Company Limited", "BSE", "India", "Consumer Discretionary", "Luxury Goods", "large", "INR", "Leading jewelry and watches company"),
    "ASIANPAINT.BO": Stock("ASIANPAINT.BO", "Asian Paints Limited", "BSE", "India", "Consumer Discretionary", "Home Improvement", "large", "INR", "India's largest paint company"),
    "PIDILITIND.BO": Stock("PIDILITIND.BO", "Pidilite Industries Limited", "BSE", "India", "Consumer Discretionary", "Home Improvement", "large", "INR", "Leading adhesives and construction chemicals company"),
    
    # India - Mid Cap Technology
    "MPHASIS.BO": Stock("MPHASIS.BO", "Mphasis Limited", "BSE", "India", "Technology", "IT Services", "mid", "INR", "IT services and solutions provider"),
    "PERSISTENT.BO": Stock("PERSISTENT.BO", "Persistent Systems Limited", "BSE", "India", "Technology", "IT Services", "mid", "INR", "Software product development services"),
    "COFORGE.BO": Stock("COFORGE.BO", "Coforge Limited", "BSE", "India", "Technology", "IT Services", "mid", "INR", "Global digital services and solutions provider"),
    
    # India - Mid Cap Finance
    "BAJAJFINSV.BO": Stock("BAJAJFINSV.BO", "Bajaj Finserv Limited", "BSE", "India", "Financials", "Financial Services", "large", "INR", "Diversified financial services company"),
    "BAJAJHLDNG.BO": Stock("BAJAJHLDNG.BO", "Bajaj Holdings & Investment Limited", "BSE", "India", "Financials", "Investment Banking", "mid", "INR", "Investment and holding company"),
    "MUTHOOTFIN.BO": Stock("MUTHOOTFIN.BO", "Muthoot Finance Limited", "BSE", "India", "Financials", "Financial Services", "mid", "INR", "Leading gold loan company"),
    
    # India - Mid Cap Pharmaceuticals
    "TORNTPHARM.BO": Stock("TORNTPHARM.BO", "Torrent Pharmaceuticals Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "mid", "INR", "Leading pharmaceutical company"),
    "CADILAHC.BO": Stock("CADILAHC.BO", "Cadila Healthcare Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "mid", "INR", "Research-based pharmaceutical company"),
    "GLENMARK.BO": Stock("GLENMARK.BO", "Glenmark Pharmaceuticals Limited", "BSE", "India", "Healthcare", "Pharmaceuticals", "mid", "INR", "Research-driven pharmaceutical company"),
    
    # India - Small Cap Emerging Companies
    "ZOMATO.BO": Stock("ZOMATO.BO", "Zomato Limited", "BSE", "India", "Consumer Discretionary", "Food Delivery", "mid", "INR", "Leading food delivery and restaurant discovery platform"),
    "NYKAA.BO": Stock("NYKAA.BO", "FSN E-Commerce Ventures Limited", "BSE", "India", "Consumer Discretionary", "E-commerce", "mid", "INR", "Leading beauty and fashion e-commerce platform"),
    "PAYTM.BO": Stock("PAYTM.BO", "One 97 Communications Limited", "BSE", "India", "Technology", "Financial Technology", "mid", "INR", "Leading digital payments and financial services platform"),
}
