//+------------------------------------------------------------------+
//| QuantLab_Export.mq5                                              |
//| Script: exports closed-bar history + symbol specs to CSV.        |
//| Output folder: <MT5 data>\Common\Files\QuantLab\                 |
//| Files:  QL_<SYMBOL>_<TF>.csv   QL_<SYMBOL>_specs.csv  QL_meta.csv|
//| NOTE: written without access to a compiler - compile it in       |
//| MetaEditor (F7) and report any error exactly as shown.           |
//+------------------------------------------------------------------+
#property copyright "QuantLab"
#property version   "1.00"
#property script_show_inputs

input string   InpSymbols    = "XAUUSD,EURUSD";    // symbol names exactly as in your broker's Market Watch
input string   InpTimeframes = "D1,H4,H1,M15";
input datetime InpFrom       = D'2018.01.01 00:00';
input int      InpChunkDays  = 90;                 // request history in chunks (safe for terminal bar limits)
input string   InpSubFolder  = "QuantLab";

//--- map text -> timeframe (PERIOD_CURRENT = unknown)
ENUM_TIMEFRAMES ParseTF(string s)
{
   StringTrimLeft(s); StringTrimRight(s);
   if(s=="M1")  return PERIOD_M1;
   if(s=="M5")  return PERIOD_M5;
   if(s=="M15") return PERIOD_M15;
   if(s=="M30") return PERIOD_M30;
   if(s=="H1")  return PERIOD_H1;
   if(s=="H4")  return PERIOD_H4;
   if(s=="D1")  return PERIOD_D1;
   return PERIOD_CURRENT;
}

string TFName(ENUM_TIMEFRAMES tf)
{
   if(tf==PERIOD_M15) return "M15";
   if(tf==PERIOD_H1)  return "H1";
   if(tf==PERIOD_H4)  return "H4";
   if(tf==PERIOD_D1)  return "D1";
   return EnumToString(tf);
}

//--- wait until the terminal has synchronised the series for this symbol/timeframe
void WaitSync(string sym, ENUM_TIMEFRAMES tf)
{
   for(int k=0; k<40; k++)
   {
      if((bool)SeriesInfoInteger(sym, tf, SERIES_SYNCHRONIZED)) return;
      Sleep(250);
   }
}

bool ExportRates(string sym, ENUM_TIMEFRAMES tf)
{
   string path = InpSubFolder + "\\QL_" + sym + "_" + TFName(tf) + ".csv";
   int fh = FileOpen(path, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh == INVALID_HANDLE) { Print("Cannot open ", path, " error ", GetLastError()); return false; }
   FileWrite(fh, "time","open","high","low","close","tick_volume","spread","real_volume");

   int    digits   = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   datetime now    = TimeTradeServer();   // TimeCurrent() = last quote time, which drops the last closed bar on weekends
   int    per      = PeriodSeconds(tf);
   datetime cursor = InpFrom;
   long   written  = 0;
   datetime lastT  = 0;

   while(cursor < now)
   {
      datetime to = cursor + (datetime)((long)InpChunkDays * 86400);
      if(to > now) to = now;
      MqlRates rates[];
      int got = -1;
      for(int attempt=0; attempt<6; attempt++)
      {
         got = CopyRates(sym, tf, cursor, to, rates);
         if(got >= 0) break;
         Sleep(500);                       // history may still be downloading
      }
      if(got > 0)
      {
         ArraySetAsSeries(rates, false);   // oldest first
         for(int i=0; i<got; i++)
         {
            if(rates[i].time <= lastT) continue;                 // skip duplicates across chunks
            if(rates[i].time + per > now) continue;              // drop the still-forming bar
            FileWrite(fh,
               TimeToString(rates[i].time, TIME_DATE|TIME_MINUTES),
               DoubleToString(rates[i].open,  digits),
               DoubleToString(rates[i].high,  digits),
               DoubleToString(rates[i].low,   digits),
               DoubleToString(rates[i].close, digits),
               (string)rates[i].tick_volume,
               (string)rates[i].spread,
               (string)rates[i].real_volume);
            lastT = rates[i].time;
            written++;
         }
      }
      cursor = to;
   }
   FileClose(fh);
   PrintFormat("%s %s: %I64d bars written -> Common\\Files\\%s", sym, TFName(tf), written, path);
   return written > 0;
}

void ExportSpecs(string sym)
{
   string path = InpSubFolder + "\\QL_" + sym + "_specs.csv";
   int fh = FileOpen(path, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh == INVALID_HANDLE) { Print("Cannot open ", path); return; }
   FileWrite(fh, "key", "value");
   FileWrite(fh, "symbol", sym);
   FileWrite(fh, "digits", (string)SymbolInfoInteger(sym, SYMBOL_DIGITS));
   FileWrite(fh, "point", DoubleToString(SymbolInfoDouble(sym, SYMBOL_POINT), 10));
   FileWrite(fh, "tick_size", DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE), 10));
   FileWrite(fh, "tick_value", DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE), 10));
   FileWrite(fh, "tick_value_profit", DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_PROFIT), 10));
   FileWrite(fh, "tick_value_loss", DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_LOSS), 10));
   FileWrite(fh, "contract_size", DoubleToString(SymbolInfoDouble(sym, SYMBOL_TRADE_CONTRACT_SIZE), 6));
   FileWrite(fh, "volume_min", DoubleToString(SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN), 6));
   FileWrite(fh, "volume_max", DoubleToString(SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX), 6));
   FileWrite(fh, "volume_step", DoubleToString(SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP), 6));
   FileWrite(fh, "swap_long", DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_LONG), 6));
   FileWrite(fh, "swap_short", DoubleToString(SymbolInfoDouble(sym, SYMBOL_SWAP_SHORT), 6));
   FileWrite(fh, "swap_mode", (string)SymbolInfoInteger(sym, SYMBOL_SWAP_MODE));   // 1 = points
   FileWrite(fh, "stops_level_points", (string)SymbolInfoInteger(sym, SYMBOL_TRADE_STOPS_LEVEL));
   FileWrite(fh, "calc_mode", (string)SymbolInfoInteger(sym, SYMBOL_TRADE_CALC_MODE));
   FileWrite(fh, "currency_base", SymbolInfoString(sym, SYMBOL_CURRENCY_BASE));
   FileWrite(fh, "currency_profit", SymbolInfoString(sym, SYMBOL_CURRENCY_PROFIT));
   FileWrite(fh, "currency_margin", SymbolInfoString(sym, SYMBOL_CURRENCY_MARGIN));
   FileWrite(fh, "description", SymbolInfoString(sym, SYMBOL_DESCRIPTION));
   FileWrite(fh, "current_spread_points", (string)SymbolInfoInteger(sym, SYMBOL_SPREAD));
   FileClose(fh);
}

void ExportMeta()
{
   string path = InpSubFolder + "\\QL_meta.csv";
   int fh = FileOpen(path, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh == INVALID_HANDLE) return;
   long offset = (long)(TimeTradeServer() - TimeGMT());
   FileWrite(fh, "key", "value");
   FileWrite(fh, "broker_company", AccountInfoString(ACCOUNT_COMPANY));
   FileWrite(fh, "server", AccountInfoString(ACCOUNT_SERVER));
   FileWrite(fh, "server_minus_gmt_seconds_now", (string)offset);   // changes with DST if the server uses DST
   FileWrite(fh, "terminal_build", (string)TerminalInfoInteger(TERMINAL_BUILD));
   FileWrite(fh, "exported_at_server_time", TimeToString(TimeTradeServer(), TIME_DATE|TIME_MINUTES|TIME_SECONDS));
   FileWrite(fh, "export_from", TimeToString(InpFrom, TIME_DATE|TIME_MINUTES));
   FileClose(fh);
}

void OnStart()
{
   FolderCreate(InpSubFolder, FILE_COMMON);
   string syms[], tfs[];
   int ns = StringSplit(InpSymbols, ',', syms);
   int nt = StringSplit(InpTimeframes, ',', tfs);
   ExportMeta();
   for(int a=0; a<ns; a++)
   {
      string sym = syms[a];
      StringTrimLeft(sym); StringTrimRight(sym);
      if(!SymbolSelect(sym, true)) { Print("Symbol not available: ", sym); continue; }
      ExportSpecs(sym);
      for(int b=0; b<nt; b++)
      {
         ENUM_TIMEFRAMES tf = ParseTF(tfs[b]);
         if(tf == PERIOD_CURRENT) { Print("Unknown timeframe: ", tfs[b]); continue; }
         WaitSync(sym, tf);
         ExportRates(sym, tf);
      }
   }
   Print("QuantLab export finished. Files are in Common\\Files\\", InpSubFolder);
   Alert("QuantLab export finished - see the Experts log and the Common\\Files\\", InpSubFolder, " folder");
}
