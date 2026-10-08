import {buttons,validate,Protocol} from './protocol.js';
const $=id=>document.getElementById(id);
let port,reader,writer,protocol,readTask,demo=false,busy=false,disconnecting=false;
let profile={dpi:800,bindings:[...buttons]};
const labelNames=['Left click','Right click','Wheel click','Side / back','Side / forward'];
for(let i=0;i<5;i++){
  const row=document.createElement('div');row.className='binding';
  const number=document.createElement('span');number.className='number';number.textContent='0'+(i+1);
  const label=document.createElement('label');label.htmlFor='binding-'+i;label.textContent=labelNames[i];
  const select=document.createElement('select');select.id='binding-'+i;
  for(const action of [...buttons,'none','keyboard']){const option=document.createElement('option');option.value=action;option.textContent=action==='keyboard'?'Shortcut':action[0].toUpperCase()+action.slice(1);select.append(option);}
  select.value=buttons[i];
  const key=document.createElement('input');key.id='key-'+i;key.placeholder='CTRL+C';key.setAttribute('aria-label',labelNames[i]+' keyboard shortcut');key.hidden=true;key.maxLength=80;
  select.addEventListener('change',()=>{key.hidden=select.value!=='keyboard';dirty();});key.addEventListener('input',dirty);
  row.append(number,label,select,key);$('bindings').append(row);
}
function notice(text,error=false){$('notice').textContent=text;$('notice').classList.toggle('error',error);}
function dirty(){notice(demo?'Demo profile changed. Connect a device to send settings.':'Changes have not been applied.');}
function updateControls(){const connected=!!protocol;$('fields').disabled=busy||(!connected&&!demo);$('connect').disabled=busy||connected;$('disconnect').hidden=!connected;$('disconnect').disabled=busy;$('save').disabled=busy||!connected;$('reload').disabled=busy||!connected;$('demo').disabled=busy||connected;$('import').disabled=busy;$('export').disabled=busy;}
function render(value){profile=validate(value);$('dpi').value=profile.dpi;$('dpi-range').value=profile.dpi;profile.bindings.forEach((action,i)=>{const keyboard=action.startsWith('key:');$('binding-'+i).value=keyboard?'keyboard':action;$('key-'+i).hidden=!keyboard;$('key-'+i).value=keyboard?action.slice(4):'';});}
function collect(){return validate({dpi:Number($('dpi').value),bindings:buttons.map((_,i)=>$('binding-'+i).value==='keyboard'?'key:'+$('key-'+i).value.trim().toUpperCase():$('binding-'+i).value)});}
async function operation(task){if(busy)return;busy=true;updateControls();try{await task();}catch(error){notice(error.message,true);}finally{busy=false;updateControls();}}
async function readLoop(){const decoder=new TextDecoder();try{while(true){const {value,done}=await reader.read();if(done)break;protocol?.feed(decoder.decode(value,{stream:true}));}}catch(error){if(!disconnecting)notice('Connection lost: '+error.message,true);}finally{reader?.releaseLock();reader=undefined;if(!disconnecting)void disconnect(true);}}
async function disconnect(lost=false){if(disconnecting)return;disconnecting=true;protocol?.close();protocol=undefined;try{if(reader)await reader.cancel();if(readTask)await readTask;writer?.releaseLock();writer=undefined;await port?.close();}catch{}finally{port=undefined;readTask=undefined;demo=false;disconnecting=false;$('light').classList.remove('connected');$('status').textContent='No device connected';$('mode').textContent='OFFLINE';updateControls();if(!lost)notice('Device disconnected.');}}
$('connect').addEventListener('click',()=>operation(async()=>{
  if(!navigator.serial || !window.isSecureContext)throw Error('Open this page in desktop Chrome or Edge on HTTPS or localhost.');
  demo=false;port=await navigator.serial.requestPort();
  try{await port.open({baudRate:115200});await port.setSignals({dataTerminalReady:true});writer=port.writable.getWriter();reader=port.readable.getReader();protocol=new Protocol(line=>writer.write(new TextEncoder().encode(line)));readTask=readLoop();
    const hello=await protocol.request('hello');if(hello.device!=='OpenMice'||hello.protocol!==1)throw Error('Selected port is not a compatible OpenMice device.');render(hello.config);$('status').textContent='OpenMice connected';$('light').classList.add('connected');$('mode').textContent='CONNECTED';notice('Profile read from the mouse. Changes apply only when you choose Apply.');
  }catch(error){await disconnect(true);throw error;}
}));
$('disconnect').addEventListener('click',()=>operation(()=>disconnect()));
$('demo').addEventListener('click',()=>{demo=true;render({dpi:800,bindings:[...buttons]});$('mode').textContent='DEMO';$('status').textContent='Demo · no device connected';notice('Demo changes stay in your browser. Connect a real device to apply them.');updateControls();});
$('dpi').addEventListener('input',()=>{$('dpi-range').value=$('dpi').value;dirty();});$('dpi-range').addEventListener('input',()=>{$('dpi').value=$('dpi-range').value;dirty();});document.querySelectorAll('[data-dpi]').forEach(button=>button.addEventListener('click',()=>{$('dpi').value=button.dataset.dpi;$('dpi-range').value=button.dataset.dpi;dirty();}));
$('profile').addEventListener('submit',event=>{event.preventDefault();void operation(async()=>{const config=collect();if(demo){profile=config;notice('Demo profile updated in this browser. No device was changed.');return;}const result=await protocol.request('set',{config});render(result.config);notice('Applied to the mouse. Choose Save to mouse to keep settings after power off.');});});
$('save').addEventListener('click',()=>operation(async()=>{const current=collect();await protocol.request('set',{config:current});const result=await protocol.request('save');render(result.config);notice('Settings saved on the mouse.');}));
$('reload').addEventListener('click',()=>operation(async()=>{const result=await protocol.request('get');render(result.config);notice('Current device settings loaded.');}));
$('export').addEventListener('click',()=>{try{const config=collect();const blob=new Blob([JSON.stringify(config,null,2)+'\n'],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='openmice-profile.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){notice(error.message,true);}});
$('import').addEventListener('change',()=>operation(async()=>{const file=$('import').files[0];try{if(!file)return;if(file.size>4096)throw Error('Profile file is too large.');render(JSON.parse(await file.text()));if(!protocol){demo=true;$('mode').textContent='DEMO';$('status').textContent='Imported profile · no device connected';}notice('Profile imported. Review it, then Apply to send it to the mouse.');}finally{$('import').value='';}}));
navigator.serial?.addEventListener('disconnect',event=>{if(event.target===port)void disconnect(true);});
updateControls();
