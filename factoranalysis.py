import numpy as np
import pandas as pd
from pathlib import Path
import yfinance as yf
from time import sleep
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import zscore

class PFA:
    def __init__(self, file: str, interval: str="1wk") -> None:
        self.logger = logging.getLogger(__name__)
        self.file = Path(file)
        self.interval = interval
        self.stocks = self._load_stocks()
        
    def _load_stocks(self) -> list:
        if self.file.exists() and self.file.is_file():
            try:
                with open(self.file, "r") as file:
                    return [stock.strip().upper() for stock in file.readlines()]
            except KeyError:
                pass
        return []
    
    def _download_data(self) -> pd.DataFrame:
        if not self.stocks:
            return pd.DataFrame()
        alldata = []
        if not Path("data").exists():
            Path("data").mkdir()
        for stock in self.stocks:
            path = Path(f"data/{stock}_{self.interval}.csv")
            if path.exists():
                alldata.append(pd.read_csv(path, index_col=0, parse_dates=True).Close.rename(stock))
                continue
            try:
                sleep(0.2)
                data = yf.download(
                    stock, 
                    interval=self.interval,
                    period="5y", 
                    auto_adjust=True, 
                    multi_level_index=False, progress=False
                )
                data.to_csv(path)
                alldata.append(data.Close.rename(stock))
            except Exception as e:
                self.logger.error(e)
                continue
        return pd.concat(alldata, axis=1, join="inner")
    
    def _get_returns(self) -> pd.DataFrame:
        if not self.stocks:
            return pd.DataFrame()
        df = self._download_data()
        if df.empty:
            return pd.DataFrame()
        return df.pct_change().fillna(0.0) * 100
    
    def get_zscores(self) -> pd.DataFrame:
        df = self._get_returns()
        if df.empty:
            return pd.DataFrame()
        return zscore(a=df, axis=0)
    
    def get_betas(self, benchmark: str="SPY", window=12) -> pd.DataFrame:
        X = self._get_returns()
        if X.empty:
            return pd.DataFrame()
        try:
            Y = (yf.download(
                benchmark, 
                interval=self.interval, 
                period="max", 
                auto_adjust=True, 
                multi_level_index=False,
                progress=False
            ).Close.pct_change().fillna(0.0) * 100).rename(benchmark)
        except Exception as e:
            self.logger.error(e)
            return pd.DataFrame()
        sample = pd.concat([X,Y], axis=1, join="inner").dropna()
        alldata = []
        for stock in sample.columns.drop(benchmark):
            betas = pd.Series(dtype=float, name=stock)
            for i in range(len(sample) - window):
                data = sample[[stock, benchmark]].iloc[i:i+window]
                cov_matrix = data.cov()[benchmark]
                beta = cov_matrix[0] / cov_matrix[1]
                betas.loc[sample.index[i+window]] = beta
            alldata.append(betas)
        return pd.concat(alldata, axis=1)
    
    def decomposition(self) -> dict:
        df = self._get_returns()
        if df.empty:
            return pd.DataFrame()
        scaler = StandardScaler()
        pca = PCA()
        pca.fit(scaler.fit_transform(df))
        exp_var = np.cumsum(pca.explained_variance_ratio_)
        comps = pca.components_
        return {
            "expvar": pd.Series(data=exp_var, index=[f"PC{i+1}" for i in range(len(exp_var))]),
            "comps": pd.DataFrame(data=comps, index=df.columns, columns=[f"PC{i+1}" for i in range(len(comps.T))])
            }
            
pfa = PFA("portfolio.txt")