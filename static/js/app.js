/**
 * Little Millennium - Nest Daycare (Kharadi Branch)
 * Enterprise ERP & CRM Client Core Engine
 */

window.LittleMillennium = {
  // Sound synthesizer using Web Audio API (Zero external assets required)
  playChime: function(type = 'success') {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      const now = audioCtx.currentTime;
      if (type === 'success') {
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.1);
        osc.frequency.exponentialRampToValueAtTime(783.99, now + 0.2);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      } else if (type === 'badge') {
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
          const o = audioCtx.createOscillator();
          const g = audioCtx.createGain();
          o.connect(g);
          g.connect(audioCtx.destination);
          o.frequency.value = freq;
          g.gain.setValueAtTime(0.12, now + (i * 0.08));
          g.gain.exponentialRampToValueAtTime(0.01, now + (i * 0.08) + 0.25);
          o.start(now + (i * 0.08));
          o.stop(now + (i * 0.08) + 0.25);
        });
      } else if (type === 'alert') {
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.setValueAtTime(330, now + 0.15);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
      }
    } catch (e) {
      // AudioContext muted or not allowed prior to user gesture
    }
  },

  // Central Branded Processing Loader
  showLoader: function(message = "Processing request...", subtext = "Little Millennium Kharadi Engine") {
    const loader = document.getElementById('central-processing-loader');
    const msgEl = document.getElementById('loader-message');
    const subEl = document.getElementById('loader-subtext');
    if (loader) {
      if (msgEl) msgEl.innerText = message;
      if (subEl) subEl.innerText = subtext;
      loader.classList.add('active');
    }
  },

  hideLoader: function() {
    const loader = document.getElementById('central-processing-loader');
    if (loader) {
      loader.classList.remove('active');
    }
  },

  // Toast notifications
  toast: function(title, message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const bgColors = {
      success: 'bg-emerald-50 border-emerald-500 text-emerald-900',
      error: 'bg-rose-50 border-rose-500 text-rose-900',
      info: 'bg-sky-50 border-sky-500 text-sky-900',
      warning: 'bg-amber-50 border-amber-500 text-amber-900'
    };

    const icons = {
      success: '✓',
      error: '✕',
      info: 'ℹ',
      warning: '⚠'
    };

    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border-l-4 shadow-lg transition-all duration-300 transform translate-y-2 opacity-0 ${bgColors[type] || bgColors.success}`;
    toast.innerHTML = `
      <span class="font-bold text-lg">${icons[type] || '•'}</span>
      <div>
        <p class="font-bold text-xs leading-tight">${title}</p>
        <p class="text-[11px] opacity-90">${message}</p>
      </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    LittleMillennium.playChime(type === 'error' ? 'alert' : 'success');

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

// Global Receipt Viewer (Official Little Millennium Fee Receipt Modal)
window.viewReceipt = function(receiptNo, date, student, classroom, parent, term, amount, method) {
  const modal = document.getElementById('receipt-modal');
  if (!modal) return;

  const setEl = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.innerText = val;
  };

  setEl('receipt-no', receiptNo || 'REC-LM-4401');
  setEl('receipt-date', date || new Date().toISOString().split('T')[0]);
  setEl('receipt-student', student || 'Aarav Mehta');
  setEl('receipt-class', classroom || 'Toddler Nest');
  setEl('receipt-parent', parent || 'Parent');
  setEl('receipt-term', term || 'Current Term');
  
  const numAmount = parseFloat(amount) || 0;
  const formatted = '₹' + numAmount.toLocaleString('en-IN', {minimumFractionDigits: 2});
  setEl('receipt-amount', formatted);
  setEl('receipt-total', formatted);
  setEl('receipt-method', method || 'UPI / Zero-Fee Passthrough');

  modal.classList.remove('hidden');
};

// Global DOM Event Binding
document.addEventListener('DOMContentLoaded', function() {
  LittleMillennium.hideLoader();

  // Attach loader to all standard forms on submit
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
      const customMsg = form.getAttribute('data-loading-msg') || 'Saving & Synchronizing...';
      LittleMillennium.showLoader(customMsg, 'Little Millennium Kharadi Campus');
    });
  });

  // Intercept data-loader links
  document.querySelectorAll('a[data-loader]').forEach(link => {
    link.addEventListener('click', function(e) {
      const msg = link.getAttribute('data-loader') || 'Loading Portal...';
      LittleMillennium.showLoader(msg);
    });
  });

  // Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('mobile-sidebar-toggle');
  const sidebar = document.getElementById('main-sidebar');
  const sidebarBackdrop = document.getElementById('sidebar-backdrop');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('-translate-x-full');
      if (sidebarBackdrop) sidebarBackdrop.classList.toggle('hidden');
    });
  }

  if (sidebarBackdrop && sidebar) {
    sidebarBackdrop.addEventListener('click', () => {
      sidebar.classList.add('-translate-x-full');
      sidebarBackdrop.classList.add('hidden');
    });
  }
});
