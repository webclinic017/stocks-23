from sqlalchemy import create_engine,text
import pandas as pd
import logging

class SQL():
    user = 'root'
    pw = 'oracle_4U'
    host = 'localhost'
    db = 'stocks'
    table = 'data'
    calendar_table = 'stock_adjust_calendar'
    engine = None
    
    def __init__(self):
        self.engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}".format(user=self.user,pw=self.pw,host=self.host,db=self.db))
    
    def insert(self, dataframe):
        dataframe.to_sql(self.table, con = self.engine, if_exists = 'append', chunksize=100)
    
    def getStockData(self, ticker, timelimit):
        logging.debug(f"Get stock data for {ticker}")
        return pd.read_sql_query(f"""
            select ticker, date, close 
            from {self.table} 
            where ticker = '{ticker}' 
            order by date desc 
            limit {timelimit}""", con=self.engine)
    
    def getLatestData(self):
        logging.debug("Get latest stock data")
        return pd.read_sql_query(f"""
            select ticker 
            from {self.table} 
            where date = (select distinct date from data order by date desc limit 1)
            and volume >100000
            and length(ticker) =3
            """, con = self.engine)

    def insertCalendarEvent(self, dataframe):
        # process df
        logging.info("insert calendar events")
        dataframe = dataframe.drop(dataframe.columns[[1, 3, 4, 5]], axis=1)
        df = pd.DataFrame(dataframe.values, columns=["ticker", "date", "percentage"])
        calendar_dict = df.to_dict(orient='records')
        # insert to db

        with self.engine.connect() as conn:
            query = text(f"""insert into {self.calendar_table}
            (ticker, date,percentage, processed) 
            values 
            (:ticker,str_to_date(:date,"%d/%m/%Y"),:percentage,0)
            """)
            for item in calendar_dict:
                try:
                    conn.execute(query,**item)
                except Exception as e:
                    logging.error(str(e))

    def adjustPrice(self):
        """
        adjust stock price after issuing additional stock
        """
        # get list of 
        logging.info("adjust stock price")
        query =f"""
            select ticker, date, percentage 
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
        sql = text(f"""
        update {self.table}
        set close = close * :percentage,
        open = open * :percentage,
        high = high * :percentage,
        low = low * :percentage
        where ticker = :ticker
        and date < str_to_date(:date, "%d/%m/%Y")
        """)
        
        update_event_sql = text(f"""
            update {self.calendar_table}
            set processed = 1
            where ticker = :ticker
            and date = str_to_date(:date, "%d/%m/%Y")
            """)
        
        with self.engine.connect() as conn:
            for event in events_dict:
                logging.info(f"Adjust price for {event['ticker']}")
                conn.execute(sql, **event)
                conn.execute(update_event_sql, **event)
