/**
 * Native HTML5 Canvas E-Signature Pad
 * Zero third-party fees (No DocuSign / Adobe Sign API costs)
 */
class DigitalSignaturePad {
  constructor(canvasId, clearBtnId, hiddenInputId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.clearBtn = document.getElementById(clearBtnId);
    this.hiddenInput = document.getElementById(hiddenInputId);
    this.isDrawing = false;
    this.hasSignature = false;

    this.init();
  }

  init() {
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    this.ctx.lineWidth = 2.5;
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';
    this.ctx.strokeStyle = '#1E293B'; // Dark slate ink

    // Mouse Events
    this.canvas.addEventListener('mousedown', (e) => this.startDrawing(e));
    this.canvas.addEventListener('mousemove', (e) => this.draw(e));
    window.addEventListener('mouseup', () => this.stopDrawing());

    // Touch Events for Mobile / Tablet iPads
    this.canvas.addEventListener('touchstart', (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
      });
      this.canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
      });
      this.canvas.dispatchEvent(mouseEvent);
    }, { passive: false });

    this.canvas.addEventListener('touchend', (e) => {
      e.preventDefault();
      const mouseEvent = new MouseEvent('mouseup', {});
      window.dispatchEvent(mouseEvent);
    }, { passive: false });

    // Clear Button
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.clear();
      });
    }
  }

  resizeCanvas() {
    const rect = this.canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    
    // Save previous drawing if any
    const dataUrl = this.hasSignature ? this.canvas.toDataURL() : null;
    
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;

    this.ctx.lineWidth = 2.5;
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';
    this.ctx.strokeStyle = '#1E293B';

    if (dataUrl) {
      const img = new Image();
      img.onload = () => {
        this.ctx.drawImage(img, 0, 0);
      };
      img.src = dataUrl;
    }
  }

  getCoordinates(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  startDrawing(e) {
    this.isDrawing = true;
    const { x, y } = this.getCoordinates(e);
    this.ctx.beginPath();
    this.ctx.moveTo(x, y);
  }

  draw(e) {
    if (!this.isDrawing) return;
    const { x, y } = this.getCoordinates(e);
    this.ctx.lineTo(x, y);
    this.ctx.stroke();
    this.hasSignature = true;
    this.updateHiddenInput();
  }

  stopDrawing() {
    if (this.isDrawing) {
      this.ctx.closePath();
      this.isDrawing = false;
      this.updateHiddenInput();
    }
  }

  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.hasSignature = false;
    if (this.hiddenInput) this.hiddenInput.value = '';
    LittleMillennium.toast('Signature Cleared', 'Please sign inside the box', 'info');
  }

  updateHiddenInput() {
    if (this.hiddenInput && this.hasSignature) {
      this.hiddenInput.value = this.canvas.toDataURL('image/png');
    }
  }
}

window.DigitalSignaturePad = DigitalSignaturePad;
