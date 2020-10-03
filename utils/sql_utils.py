from sqlalchemy import create_engine,text,types,DateTime
import pandas as pd
import logging

class SQL():
    user = 'root'
    pw = 'oracle_4U'
    host = 'localhost'
    db = 'stocks'
    table = 'data'
    calendar_table = 'stock_events'
    engine = None
    
    def __init__(self):
        self.engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}".format(user=self.user,pw=self.pw,host=self.host,db=self.db))
    
    def insert(self, dataframe):
        dataframe.to_sql(self.table, con = self.engine, if_exists = 'append', chunksize=100,
            )
    
    def getStockData(self, ticker, timelimit):
        logging.debug(f"Get stock data for {ticker}")
        return pd.read_sql_query(f"""
            select ticker, date, open, high, low, close, volume
            from {self.table} 
            where ticker = '{ticker}' 
            order by date desc 
            limit {timelimit}""", con=self.engine)
    
    def getLatestData(self):
        logging.debug("Get latest stock data")
        sector_list = pd.read_sql_query(f"""
            select distinct sector 
            from ticker_data
            """, con = self.engine)['sector'].tolist()

        dfs ={}
        for sector in sector_list:
            df = pd.read_sql_query(f"""
            select ticker 
            from {self.table}
            where ticker in 
            (select ticker from ticker_data
            where sector = '{sector}') 
            and date = (select distinct date from data order by date desc limit 1)
            and volume >100000
            and length(ticker) =3
            """, con = self.engine)
            dfs[sector]=df
        return dfs

    def insertCalendarEvent(self, dataframe):
        # process df
        logging.info("insert calendar events")
        df = pd.read_sql_query(f"""
            select * from {self.calendar_table}
            """, con = self.engine)
        dataframe = (
            dataframe.merge(
                df,
                on = ['ticker', 'event', 'date', 'execution_date'],
                how = 'left',
                indicator=True
            ).query('_merge == "left_only"').drop(columns='_merge')
        )
        dataframe['detail']=dataframe['detail_x']
        dataframe['processed']=dataframe['processed_x']
        dataframe=dataframe.drop(['processed_x', 'processed_y', 'detail_x', 'detail_y'], axis=1)
        print(dataframe)
        dataframe.to_sql(self.calendar_table, con = self.engine, if_exists = 'append',index=False,
            dtype={
            'ticker':types.VARCHAR(length=15),
            'event':types.VARCHAR(length=50),
            'date':DateTime(),
            'execution_date':types.VARCHAR(length=50),
            'detail':types.Float(precision=3,asdecimal=True),
            'processed':types.INTEGER()
            })

    def adjustPrice(self):
        """
        adjust stock price after dividends
        """
        # get list of 
        logging.info("adjust stock price")
        query =f"""
            select ticker,event, date, detail 
            from {self.calendar_table}
            where processed = 0
            and date < curdate()
            """
        events = pd.read_sql_query(query, con = self.engine)

        logging.info(f"Events list length: {len(events)}")
        
        if len(events) ==0:
            return 

        events['date'] = events['date'].dt.strftime("%d/%m/%Y")
        
        events_dict = events.to_dict(orient='records')
        # sql = text(f"""
        # update {self.table}
        # set close = close * :percentage,
        # open = open * :percentage,
        # high = high * :percentage,
        # low = low * :percentage
        # where ticker = :ticker
        # and date < str_to_date(:date, "%d/%m/%Y")
        # """)
        
        sql_cash = text(f"""
            update {self.table}
            set close = (close*close) / (close + :detail),
            open = (open * open) / (open+ :detail),
            high = (high * high) / (high + :detail),
            low = (low * low) / (low + :detail)
            where ticker = :ticker
            and date < str_to_date(:date, "%d/%m/%Y")
            """)
        sql_stock = text(f"""
            update {self.table}
            set close = close / :detail,
            open = open / :detail,
            high = high / :detail,
            low = low / :detail
            where ticker = :ticker
            and date < str_to_date(:date, "%d/%m/%Y")
            """)
        update_event_sql = text(f"""
            update {self.calendar_table}
            set processed = 1
            where ticker = :ticker
            and date = str_to_date(:date, "%d/%m/%Y")
            and event = :event
            """)
        
        with self.engine.connect() as conn:
            for event in events_dict:
                logging.info(f"Adjust price for {event['ticker']} event type: {event['event']}")
                if (event['event'] == 'Cash Dividend'):
                    conn.execute(sql_cash, **event)
                else:
                    conn.execute(sql_stock, **event)
                conn.execute(update_event_sql, **event)
