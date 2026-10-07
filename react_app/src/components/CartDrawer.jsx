import React from 'react';
import { useFolliCare } from '../context/FolliCareContext';
import { X, Trash2, ShoppingBag, ArrowRight } from 'lucide-react';

export function CartDrawer({ isOpen, onClose }) {
  const { cart, removeFromCart, addToCart } = useFolliCare();
  const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(8px)',
      display: 'flex', justifyContent: 'flex-end',
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div style={{
        width: '450px', maxWidth: '100%', height: '100%',
        background: 'var(--bg-secondary)', borderLeft: '1px solid var(--border-color)',
        display: 'flex', flexDirection: 'column', padding: '24px',
        boxShadow: '-10px 0 30px rgba(0,0,0,0.5)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '16px', borderBottom: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShoppingBag size={20} color="var(--accent-color)" />
            <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Shopping Bag ({cart.length})</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {cart.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '10px' }}>🌿</div>
              <p>Your bag is currently empty.</p>
              <p style={{ fontSize: '0.85rem' }}>Ask FolliCare Copilot or explore our clinical catalog!</p>
            </div>
          ) : (
            cart.map(item => (
              <div key={item.id} style={{
                display: 'flex', alignItems: 'center', gap: '14px',
                background: 'var(--bg-card)', padding: '12px 16px',
                borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)'
              }}>
                <div style={{ fontSize: '1.8rem' }}>{item.icon || '🌿'}</div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>{item.name}</h4>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-color)', fontWeight: 600 }}>
                    ${parseFloat(item.price).toFixed(2)} × {item.quantity}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    onClick={() => removeFromCart(item.id)}
                    style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {cart.length > 0 && (
          <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', fontSize: '1.1rem', fontWeight: 800 }}>
              <span>Total Estimated:</span>
              <span style={{ color: 'var(--accent-color)' }}>${total.toFixed(2)}</span>
            </div>
            <button
              onClick={() => alert(`Order placed for $${total.toFixed(2)}! Formulations dispatched.`)}
              style={{
                width: '100%', padding: '14px',
                background: 'var(--accent-color)', color: '#ffffff',
                border: 'none', borderRadius: 'var(--radius-md)',
                fontWeight: 800, fontSize: '1rem', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
              }}
            >
              <span>Proceed to Checkout</span>
              <ArrowRight size={18} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
