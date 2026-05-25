const API = 'http://127.0.0.1:8000';
let token = localStorage.getItem('token');
let usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
let carrito = [];
let mesaSeleccionada = null;
let todasLasMesas = [];

// =====================
// INICIO
// =====================
window.onload = () => {
  if (token && usuario) {
    mostrarPantalla('principal');
    document.getElementById('saludo-usuario').textContent = `Hola, ${usuario.nombre} 👋`;
    cargarMesas();
  } else {
    mostrarPantalla('auth');
  }
};

// =====================
// UTILIDADES
// =====================
function mostrarPantalla(nombre) {
  document.querySelectorAll('.pantalla').forEach(p => p.classList.remove('activa'));
  document.getElementById(`pantalla-${nombre}`).classList.add('activa');
}

function mostrarSeccion(nombre) {
  document.querySelectorAll('.seccion').forEach(s => s.classList.remove('activa'));
  document.getElementById(`seccion-${nombre}`).classList.add('activa');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('activo'));
  event.target.classList.add('activo');

  if (nombre === 'menu') cargarMenu();
  if (nombre === 'mis-pedidos') cargarMisPedidos();
}

function mostrarTab(tab) {
  document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('form-registro').style.display = tab === 'registro' ? 'block' : 'none';
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('activo'));
  event.target.classList.add('activo');
}

function cerrarModal(id) {
  document.getElementById(id).style.display = 'none';
}

// =====================
// AUTH
// =====================
async function login() {
  const correo = document.getElementById('login-correo').value;
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('auth-error');

  try {
    const res = await fetch(`${API}/usuarios/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo, password })
    });
    const data = await res.json();
    if (!res.ok) { errorEl.textContent = data.detail || 'Error al iniciar sesión'; return; }

    token = data.access_token;
    localStorage.setItem('token', token);

    const perfil = await fetch(`${API}/usuarios/yo`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    usuario = await perfil.json();
    localStorage.setItem('usuario', JSON.stringify(usuario));

    document.getElementById('saludo-usuario').textContent = `Hola, ${usuario.nombre} 👋`;
    mostrarPantalla('principal');
    cargarMesas();
  } catch (e) {
    errorEl.textContent = 'Error de conexión';
  }
}

async function registro() {
  const nombre = document.getElementById('reg-nombre').value;
  const correo = document.getElementById('reg-correo').value;
  const password = document.getElementById('reg-password').value;
  const errorEl = document.getElementById('auth-error');

  try {
    const res = await fetch(`${API}/usuarios/registro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, correo, password })
    });
    const data = await res.json();
    if (!res.ok) { errorEl.textContent = data.detail || 'Error al registrarse'; return; }

    errorEl.style.color = 'green';
    errorEl.textContent = '✅ Cuenta creada. Inicia sesión.';
    mostrarTab('login');
  } catch (e) {
    errorEl.textContent = 'Error de conexión';
  }
}

function cerrarSesion() {
  token = null;
  usuario = null;
  localStorage.removeItem('token');
  localStorage.removeItem('usuario');
  mostrarPantalla('auth');
}

// =====================
// MESAS
// =====================
async function cargarMesas() {
  try {
    const res = await fetch(`${API}/mesas/`);
    todasLasMesas = await res.json();
    renderizarMapa(todasLasMesas);
  } catch (e) {
    console.error('Error cargando mesas', e);
  }
}

function renderizarMapa(mesas) {
  const contenedor = document.getElementById('mapa-mesas');
  contenedor.innerHTML = '';

  mesas.forEach(mesa => {
    const bloqueada = mesa.estado === 'ocupada';
    const card = document.createElement('div');
    card.className = `mesa-card estado-${mesa.estado} ${bloqueada ? 'bloqueada' : ''}`;

    const iconos = { pequena: '🪑🪑', mediana: '🪑🪑🪑🪑', grande: '🪑x6' };
    const estadoTexto = {
      libre: 'Libre',
      ocupada: 'Ocupada',
      reservada: 'Reservada',
      esperando_pedido: 'Esperando pedido',
      preparando: 'Preparando'
    };

    card.innerHTML = `
      <div class="mesa-numero">Mesa ${mesa.numero}</div>
      <div class="mesa-capacidad">${iconos[mesa.tipo] || ''} ${mesa.capacidad} personas</div>
      <div class="mesa-estado ${mesa.estado}">${estadoTexto[mesa.estado] || mesa.estado}</div>
    `;

    if (!bloqueada) {
      card.onclick = () => abrirModalReserva(mesa);
    }

    contenedor.appendChild(card);
  });
}

function abrirModalReserva(mesa) {
  mesaSeleccionada = mesa;
  document.getElementById('modal-mesa-num').textContent = mesa.numero;
  document.getElementById('reserva-personas').max = mesa.capacidad;

  const ahora = new Date();
  ahora.setMinutes(ahora.getMinutes() - ahora.getTimezoneOffset());
  document.getElementById('reserva-fecha').min = ahora.toISOString().slice(0, 16);
  document.getElementById('reserva-fecha').value = ahora.toISOString().slice(0, 16);

  document.getElementById('reserva-error').textContent = '';
  document.getElementById('modal-reserva').style.display = 'flex';
}

async function confirmarReserva() {
  const personas = parseInt(document.getElementById('reserva-personas').value);
  const fecha = document.getElementById('reserva-fecha').value;
  const errorEl = document.getElementById('reserva-error');

  if (!fecha) { errorEl.textContent = 'Selecciona una fecha'; return; }

  try {
    const res = await fetch(`${API}/reservaciones/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        mesa_id: mesaSeleccionada.id,
        num_personas: personas,
        fecha_hora: new Date(fecha).toISOString()
      })
    });
    const data = await res.json();
    if (!res.ok) { errorEl.textContent = data.detail || 'Error al reservar'; return; }

    cerrarModal('modal-reserva');
    cargarMesas();
    alert(`✅ Mesa ${mesaSeleccionada.numero} reservada exitosamente`);
  } catch (e) {
    errorEl.textContent = 'Error de conexión';
  }
}

// =====================
// RECOMENDACIONES
// =====================
async function cargarRecomendaciones() {
  try {
    const res = await fetch(`${API}/recomendaciones/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();

    if (!data.recomendaciones || data.recomendaciones.length === 0) return;

    const contenedor = document.getElementById('seccion-menu');
    const existing = document.getElementById('bloque-recomendaciones');
    if (existing) existing.remove();

    const bloque = document.createElement('div');
    bloque.id = 'bloque-recomendaciones';
    bloque.innerHTML = `
      <div style="background: linear-gradient(135deg, #0a1628, #1a3a5c); border-radius: 12px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #c9a84c;">
        <h4 style="color: #c9a84c; margin-bottom: 6px;">⭐ Para ti, ${usuario.nombre}</h4>
        <p style="color: #ccc; font-size: 0.85rem; margin-bottom: 16px;">${data.mensaje}</p>
        <div class="menu-grid">
          ${data.recomendaciones.map(item => `
            <div class="menu-item" style="border-top-color: #c9a84c;">
              <h4>${item.nombre}</h4>
              <p style="color:#888; font-size:0.8rem">${item.categoria}</p>
              <div class="precio">$${item.precio.toFixed(2)}</div>
              <button onclick="agregarAlCarrito(${item.id}, '${item.nombre}', ${item.precio})">+ Agregar</button>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    contenedor.insertBefore(bloque, contenedor.firstChild.nextSibling);
  } catch (e) {
    console.error('Error cargando recomendaciones', e);
  }
}

// =====================
// MENÚ
// =====================
async function cargarMenu() {
  try {
    const res = await fetch(`${API}/menu/`);
    const items = await res.json();
    renderizarMenu(items);
    poblarSelectMesa();
    cargarRecomendaciones();
  } catch (e) {
    console.error('Error cargando menú', e);
  }
}

function renderizarMenu(items) {
  const contenedor = document.getElementById('categorias-menu');
  contenedor.innerHTML = '';

  const categorias = [...new Set(items.map(i => i.categoria))];
  categorias.forEach(cat => {
    const titulo = document.createElement('div');
    titulo.className = 'categoria-titulo';
    titulo.textContent = cat;
    contenedor.appendChild(titulo);

    const grid = document.createElement('div');
    grid.className = 'menu-grid';

    items.filter(i => i.categoria === cat).forEach(item => {
      const card = document.createElement('div');
      card.className = 'menu-item';
      card.innerHTML = `
        <h4>${item.nombre}</h4>
        <p>${item.descripcion || ''}</p>
        <div class="precio">$${item.precio.toFixed(2)}</div>
        <button onclick="agregarAlCarrito(${item.id}, '${item.nombre}', ${item.precio})">+ Agregar</button>
      `;
      grid.appendChild(card);
    });

    contenedor.appendChild(grid);
  });
}

function agregarAlCarrito(id, nombre, precio) {
  const existente = carrito.find(i => i.id === id);
  if (existente) {
    existente.cantidad++;
  } else {
    carrito.push({ id, nombre, precio, cantidad: 1 });
  }
  actualizarCarritoBar();
}

function actualizarCarritoBar() {
  const total = carrito.reduce((s, i) => s + i.cantidad, 0);
  const bar = document.getElementById('carrito-bar');
  bar.style.display = total > 0 ? 'flex' : 'none';
  document.getElementById('carrito-count').textContent = `${total} item${total !== 1 ? 's' : ''}`;
}

function mostrarCarrito() {
  const contenedor = document.getElementById('carrito-items');
  contenedor.innerHTML = '';
  let total = 0;

  carrito.forEach(item => {
    total += item.precio * item.cantidad;
    const div = document.createElement('div');
    div.className = 'carrito-item';
    div.innerHTML = `<span>${item.nombre} x${item.cantidad}</span><span>$${(item.precio * item.cantidad).toFixed(2)}</span>`;
    contenedor.appendChild(div);
  });

  document.getElementById('carrito-total').textContent = total.toFixed(2);
  document.getElementById('pedido-error').textContent = '';
  document.getElementById('modal-carrito').style.display = 'flex';
}

function poblarSelectMesa() {
  const select = document.getElementById('carrito-mesa');
  select.innerHTML = '<option value="">Sin mesa asignada</option>';
  todasLasMesas.filter(m => m.estado === 'libre' || m.estado === 'reservada').forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = `Mesa ${m.numero} (${m.capacidad} personas)`;
    select.appendChild(opt);
  });
}

async function enviarPedido() {
  const mesaId = document.getElementById('carrito-mesa').value;
  const errorEl = document.getElementById('pedido-error');

  if (carrito.length === 0) { errorEl.textContent = 'Tu carrito está vacío'; return; }

  const body = {
    mesa_id: mesaId ? parseInt(mesaId) : null,
    items: carrito.map(i => ({ item_id: i.id, cantidad: i.cantidad }))
  };

  try {
    const res = await fetch(`${API}/pedidos/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) { errorEl.textContent = data.detail || 'Error al enviar pedido'; return; }

    carrito = [];
    actualizarCarritoBar();
    cerrarModal('modal-carrito');
    cargarMesas();
    alert(`✅ Pedido #${data.id} enviado. Total: $${data.total.toFixed(2)}`);
  } catch (e) {
    errorEl.textContent = 'Error de conexión';
  }
}

// =====================
// MIS PEDIDOS
// =====================
async function cargarMisPedidos() {
  try {
    const res = await fetch(`${API}/pedidos/mis-pedidos`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const pedidos = await res.json();
    renderizarPedidos(pedidos);
  } catch (e) {
    console.error('Error cargando pedidos', e);
  }
}

function renderizarPedidos(pedidos) {
  const contenedor = document.getElementById('lista-pedidos');
  if (pedidos.length === 0) {
    contenedor.innerHTML = '<p style="color:#888">No tienes pedidos aún.</p>';
    return;
  }

  contenedor.innerHTML = pedidos.map(p => `
    <div class="pedido-card">
      <span class="pedido-estado estado-${p.estado}">${p.estado.toUpperCase()}</span>
      <p>Pedido #${p.id} — <strong>$${p.total.toFixed(2)}</strong></p>
      <p style="font-size:0.8rem;color:#888">${new Date(p.fecha_creacion).toLocaleString('es-MX')}</p>
    </div>
  `).join('');
}