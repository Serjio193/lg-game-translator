'use strict';
var crypto=require('crypto');
function equal(a,b) {
  var x=Buffer.from(a||''),y=Buffer.from(b||'');
  return x.length===y.length && x.length>0 && crypto.timingSafeEqual(x,y);
}
function create(clock) {
  clock=clock||Date.now;
  var pinHash=null,until=0,failures=0,lockedUntil=0,sessions=Object.create(null);
  function prune() {Object.keys(sessions).forEach(function (key) {if(sessions[key]<clock()) delete sessions[key];});}
  return {
    newPin:function () {
      if(clock()<lockedUntil) throw new Error('Подождите перед созданием нового PIN');
      var number;
      do {number=crypto.randomBytes(4).readUInt32BE(0);} while(number>=4294000000);
      var pin=('000000'+(number%1000000)).slice(-6);
      pinHash=crypto.createHash('sha256').update(pin).digest('hex');
      until=clock()+300000;failures=0;
      return {pin:pin,expiresAt:until};
    },
    pair:function (pin) {
      if(clock()<lockedUntil) throw new Error('Слишком много попыток. Подождите 30 секунд');
      var hash=typeof pin==='string'&&/^[0-9]{6}$/.test(pin)
        ? crypto.createHash('sha256').update(pin).digest('hex') : '';
      if(!pinHash||clock()>until||!equal(hash,pinHash)) {
        if(++failures>=5) {lockedUntil=clock()+30000;pinHash=null;}
        throw new Error('Неверный или истёкший PIN. Откройте подключение на ТВ');
      }
      prune();if(Object.keys(sessions).length>=16) throw new Error('Слишком много подключений');
      var token=crypto.randomBytes(32).toString('hex');sessions[token]=clock()+8*3600000;
      pinHash=null;return token;
    },
    valid:function (token) {prune();return typeof token==='string'&&!!sessions[token];},
    logout:function (token) {delete sessions[token];},
    revoke:function () {sessions=Object.create(null);pinHash=null;},
    equal:equal
  };
}
exports.create=create;
exports.equal=equal;
