const video = document.getElementById('camera');
const canvas = document.getElementById('canvas');
const previews = document.getElementById('previews');
const count = document.getElementById('count');
const message = document.getElementById('message');
const images = [];
let stream;

async function startCamera(){
  try {
    stream = await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},facingMode:'user'},audio:false});
    video.srcObject = stream;
  } catch(e) { message.textContent = 'Camera permission is required. Open this page in a browser that allows camera access.'; message.className='message error'; }
}
startCamera();

document.getElementById('capture').onclick = () => {
  if(images.length >= 5) return;
  canvas.width = video.videoWidth || 640; canvas.height = video.videoHeight || 480;
  canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
  const data = canvas.toDataURL('image/jpeg',0.88);
  images.push(data);
  const img = document.createElement('img'); img.src=data; previews.appendChild(img);
  count.textContent = `${images.length} / 3 minimum`;
};

document.getElementById('save').onclick = async () => {
  const employee_code = document.getElementById('employee_code').value.trim();
  const full_name = document.getElementById('full_name').value.trim();
  if(!employee_code || !full_name || images.length < 3){
    message.textContent='Enter Employee ID, full name, and capture at least 3 photos.'; message.className='message error'; return;
  }
  message.textContent='Creating employee…'; message.className='message';
  const body = {employee_code, full_name, department:document.getElementById('department').value.trim(), email:document.getElementById('email').value.trim()};
  let r = await fetch('/api/employees',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(body)});
  if(r.status===401){location.href='/login';return;}
  let j = await r.json();
  if(!r.ok){message.textContent=j.error||'Could not create employee.';message.className='message error';return;}
  r = await fetch(`/api/employees/${j.id}/enroll`,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify({images})});
  j = await r.json();
  if(!r.ok || !j.embeddings_saved){message.textContent=j.error||'No usable face was detected. Try again with better lighting.';message.className='message error';return;}
  message.textContent=`Success! ${j.embeddings_saved} face samples enrolled for ${full_name}.`;message.className='message success-msg';
  images.length=0; previews.innerHTML=''; count.textContent='0 / 3 minimum';
};
window.addEventListener('beforeunload',()=>stream?.getTracks().forEach(t=>t.stop()));
