"""Canonical quote QC. Synthetic fixture acceptance is not market validation."""
from math import isfinite

def quote_reasons(row,now_ms,*,max_age_ms=5000,max_alignment_ms=1000,max_relative_spread=.4):
    required=['bid','ask','bid_size','ask_size','quote_timestamp_ms','underlying_timestamp_ms','expiry_ms','forward','discount','contract_size','strike']
    if any(k not in row or row[k] is None for k in required):return ['MISSING_FIELD']
    if any(not isinstance(row[k],(int,float)) or isinstance(row[k],bool) or not isfinite(row[k]) for k in required):return ['NONFINITE_FIELD']
    reasons=[]
    if row.get('mode') not in ['SYNTHETIC','OBSERVED']:reasons.append('UNKNOWN_DATA_MODE')
    if row.get('style')!='european' or row.get('instrument_type')!='linear':reasons.append('UNSUPPORTED_CONTRACT')
    if row.get('kind') not in ['call','put']:reasons.append('INVALID_OPTION_KIND')
    if row.get('quote_currency')!=row.get('settlement_currency'):reasons.append('CURRENCY_MISMATCH')
    if not row.get('quote_currency'):reasons.append('MISSING_CURRENCY')
    if row['forward']<=0 or row['discount']<=0 or row['contract_size']<=0 or row['strike']<=0:reasons.append('INVALID_CONVENTION')
    if row['bid']<0 or row['ask']<=0:reasons.append('INVALID_PRICE')
    if row['bid']>row['ask']:reasons.append('CROSSED_BOOK')
    if row['bid']==row['ask']:reasons.append('LOCKED_BOOK')
    if row['bid_size']<=0 or row['ask_size']<=0:reasons.append('MISSING_EXECUTABLE_SIZE')
    if row['expiry_ms']<=now_ms:reasons.append('EXPIRED')
    if row['quote_timestamp_ms']>now_ms:reasons.append('FUTURE_TIMESTAMP')
    if row['underlying_timestamp_ms']>now_ms:reasons.append('FUTURE_UNDERLYING_TIMESTAMP')
    if now_ms-row['quote_timestamp_ms']>max_age_ms:reasons.append('STALE_QUOTE')
    if abs(row['quote_timestamp_ms']-row['underlying_timestamp_ms'])>max_alignment_ms:reasons.append('UNALIGNED_UNDERLYING')
    mid=(row['bid']+row['ask'])/2
    if mid>0 and (row['ask']-row['bid'])/mid>max_relative_spread:reasons.append('WIDE_SPREAD')
    if row.get('kind') in ['call','put'] and row['forward']>0 and row['strike']>0 and row['discount']>0:
        sign=1 if row['kind']=='call' else -1
        lower=row['discount']*max(sign*(row['forward']-row['strike']),0)
        upper=row['discount']*(row['forward'] if sign==1 else row['strike'])
        if not lower-1e-8<=mid<=upper+1e-8:reasons.append('MID_OUTSIDE_MODEL_BOUNDS')
    return reasons
