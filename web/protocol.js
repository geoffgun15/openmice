export const buttons = ['left','right','middle','back','forward'];
const mouseActions = [...buttons,'none'];
const keys = new Set([...Array.from({length:26},(_,i)=>String.fromCharCode(65+i)),...Array.from({length:10},(_,i)=>String(i)), 'CTRL','SHIFT','ALT','GUI','SPACE','ENTER','ESC','TAB','BACKSPACE','UP','DOWN','LEFT','RIGHT']);
export function validate(config) {
  if (!config || typeof config !== 'object' || Object.keys(config).sort().join(',') !== 'bindings,dpi') throw Error('Expected dpi and bindings.');
  if (!Number.isInteger(config.dpi) || config.dpi<50 || config.dpi>26000 || config.dpi%50) throw Error('DPI must be 50–26,000 in steps of 50.');
  if (!Array.isArray(config.bindings) || config.bindings.length!==5) throw Error('Exactly five bindings are required.');
  for (const action of config.bindings) {
    if (mouseActions.includes(action)) continue;
    if (typeof action !== 'string' || !action.startsWith('key:')) throw Error('Invalid binding.');
    const chord = action.slice(4).split('+');
    if (!chord.length || chord.length>6 || new Set(chord).size!==chord.length || chord.some(key=>!keys.has(key))) throw Error('Invalid keyboard shortcut: '+action.slice(4));
  }
  return {dpi:config.dpi,bindings:[...config.bindings]};
}
export class Protocol {
  constructor(write, timeout=5000) {this.write=write;this.timeout=timeout;this.next=1;this.pending=new Map();this.buffer='';this.discard=false;}
  request(cmd, extra={}) {
    const id=this.next++;
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{this.pending.delete(id);reject(Error('Device did not reply. Check the mouse connection.'));},this.timeout);
      this.pending.set(id,{resolve,reject,timer});
      Promise.resolve().then(()=>this.write(JSON.stringify({id,cmd,...extra})+'\n')).catch(error=>{clearTimeout(timer);this.pending.delete(id);reject(error);});
    });
  }
  feed(chunk) {
    for (const character of chunk) {
      if(character==='\n') {
        const line=this.buffer;this.buffer='';const discard=this.discard;this.discard=false;
        if(discard || !line) continue;
        let message;try{message=JSON.parse(line);}catch{continue;}
        const pending=this.pending.get(message.id);if(!pending)continue;
        clearTimeout(pending.timer);this.pending.delete(message.id);
        if(message.ok===true)pending.resolve(message);else pending.reject(Error(message.error||'Device rejected the request.'));
      } else if(!this.discard) {
        if(this.buffer.length>=1024){this.buffer='';this.discard=true;}else this.buffer+=character;
      }
    }
  }
  close() {for(const item of this.pending.values()){clearTimeout(item.timer);item.reject(Error('Device disconnected.'));}this.pending.clear();this.buffer='';this.discard=false;}
}
