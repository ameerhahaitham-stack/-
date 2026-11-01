//+------------------------------------------------------------------+
//| QuantLab_CalcCheck.mq5                                           |
//| Script: asks the terminal what 1 lot really earns per price move |
//| (OrderCalcProfit) and what margin it needs, then writes          |
//| Common\Files\QuantLab\QL_calc_check.csv and prints to Experts.   |
//| NOT compiled by the author - compile in MetaEditor (F7) first.   |
//+------------------------------------------------------------------+
#property script_show_inputs
input string InpSymbols = "XAUUSD,EURUSD";
input string InpSubFolder = "QuantLab";

void OnStart()
{
   FolderCreate(InpSubFolder, FILE_COMMON);
   int fh = FileOpen(InpSubFolder + "\\QL_calc_check.csv", FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ',');
   if(fh == INVALID_HANDLE) { Print("Cannot open output file, error ", GetLastError()); return; }
   FileWrite(fh, "symbol","bid","ask","move_px","profit_buy_1lot_usd","value_per_px_per_lot","margin_buy_1lot","contract_size","tick_size","tick_value");
   string syms[];
   int n = StringSplit(InpSymbols, ',', syms);
   for(int i=0; i<n; i++)
   {
      string s = syms[i]; StringTrimLeft(s); StringTrimRight(s);
      if(!SymbolSelect(s, true)) { Print("Symbol not available: ", s); continue; }
      double bid = SymbolInfoDouble(s, SYMBOL_BID);
      double pt  = SymbolInfoDouble(s, SYMBOL_POINT);
      double move = (StringFind(s, "XAU") >= 0) ? 1.00 : 0.01000;     // 1.00 for gold, 100 pips for EURUSD
      double profit = 0.0, margin = 0.0;
      bool ok1 = OrderCalcProfit(ORDER_TYPE_BUY, s, 1.0, bid, bid + move, profit);
      bool ok2 = OrderCalcMargin(ORDER_TYPE_BUY, s, 1.0, SymbolInfoDouble(s, SYMBOL_ASK), margin);
      double vpp = (ok1 && move > 0) ? profit / move : 0.0;
      PrintFormat("%s: 1 lot, price move %.5f => profit %.4f USD  => %.4f USD per 1.00 price move per lot | margin %.2f | ok=%d/%d",
                  s, move, profit, vpp, margin, ok1, ok2);
      FileWrite(fh, s, DoubleToString(bid,5), DoubleToString(SymbolInfoDouble(s,SYMBOL_ASK),5), DoubleToString(move,5),
                DoubleToString(profit,4), DoubleToString(vpp,4), DoubleToString(margin,2),
                DoubleToString(SymbolInfoDouble(s,SYMBOL_TRADE_CONTRACT_SIZE),2),
                DoubleToString(SymbolInfoDouble(s,SYMBOL_TRADE_TICK_SIZE),8), DoubleToString(SymbolInfoDouble(s,SYMBOL_TRADE_TICK_VALUE),8));
   }
   FileClose(fh);
   Alert("QuantLab calc check finished - see Experts log and Common\\Files\\", InpSubFolder, "\\QL_calc_check.csv");
}
