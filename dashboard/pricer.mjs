// Independent browser BSM benchmark. Normal CDF approximation, not Python output lookup.
export function normalCDF(x){
 const z=Math.abs(x),t=1/(1+.2316419*z);
 const tail=Math.exp(-z*z/2)/Math.sqrt(2*Math.PI)*t*(.319381530+t*(-.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));
 return x>=0?1-tail:tail;
}
export function price(s,k,t,r,v,q=0,kind='call'){
 if(![s,k,t,r,v,q].every(Number.isFinite)||s<=0||k<=0||t<0||v<0||!['call','put'].includes(kind))throw Error('Enter finite inputs, positive spot/strike, and nonnegative time/volatility.');
 const intrinsic=x=>Math.max(kind==='call'?x-k:k-x,0);
 if(t===0)return intrinsic(s);
 if(v===0)return Math.exp(-r*t)*intrinsic(s*Math.exp((r-q)*t));
 const d1=(Math.log(s/k)+(r-q+v*v/2)*t)/(v*Math.sqrt(t)),d2=d1-v*Math.sqrt(t);
 return kind==='call'?s*Math.exp(-q*t)*normalCDF(d1)-k*Math.exp(-r*t)*normalCDF(d2):k*Math.exp(-r*t)*normalCDF(-d2)-s*Math.exp(-q*t)*normalCDF(-d1);
}
