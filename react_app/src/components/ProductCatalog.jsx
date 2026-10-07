import React from 'react';
import { useFolliCare } from '../context/FolliCareContext';

export function ProductCard({ product }) {
  const { addToCart } = useFolliCare();

  return (
    <div style={{
      background: 'var(--bg-card)', backdropFilter: 'blur(12px)',
      border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)',
      padding: '24px', display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden'
    }}>
      <span style={{
        position: 'absolute', top: '16px', right: '16px',
        background: 'var(--bg-accent)', color: 'var(--accent-color)',
        fontSize: '0.75rem', fontWeight: 700, padding: '4px 10px',
        borderRadius: '9999px', border: '1px solid var(--border-color)'
      }}>
        {product.hairConcern || 'Trichologist Tested'}
      </span>

      <div style={{ fontSize: '3rem', textAlign: 'center', marginBottom: '16px' }}>
        {product.icon || '🌿'}
      </div>

      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>
        {product.name}
      </h3>

      <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '16px', flexGrow: 1 }}>
        {product.description}
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
        {(product.activeIngredients || []).slice(0, 3).map((ing, idx) => (
          <span key={idx} style={{
            background: 'var(--bg-secondary)', color: 'var(--text-muted)',
            fontSize: '0.72rem', fontWeight: 600, padding: '3px 8px',
            borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)'
          }}>
            {ing}
          </span>
        ))}
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginTop: 'auto', paddingTop: '14px', borderTop: '1px solid var(--border-color)'
      }}>
        <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--accent-color)' }}>
          ${product.price.toFixed(2)}
        </div>
        <button
          onClick={() => addToCart(product, 1)}
          style={{
            background: 'var(--accent-color)', color: '#ffffff', border: 'none',
            padding: '8px 16px', borderRadius: 'var(--radius-md)', fontWeight: 700,
            cursor: 'pointer'
          }}
        >
          Add to Bag
        </button>
      </div>
    </div>
  );
}

export function ProductCatalog() {
  const { products } = useFolliCare();
  const [filter, setFilter] = React.useState('All');

  const filtered = filter === 'All'
    ? products
    : products.filter(p => (p.category && p.category.toLowerCase().includes(filter.toLowerCase())) || (p.hairConcern && p.hairConcern.toLowerCase().includes(filter.toLowerCase())));

  return (
    <section style={{ maxWidth: '1200px', margin: '0 auto 60px', padding: '0 32px' }}>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '30px', justifyContent: 'center' }}>
        {['All', 'Scalp Care', 'Shampoo', 'Treatments', 'Hair Fall'].map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            style={{
              background: filter === cat ? 'var(--accent-color)' : 'var(--bg-secondary)',
              color: filter === cat ? '#ffffff' : 'var(--text-secondary)',
              border: '1px solid var(--border-color)', padding: '8px 16px',
              borderRadius: '9999px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer'
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '24px'
      }}>
        {filtered.map(prod => (
          <ProductCard key={prod.id} product={prod} />
        ))}
      </div>
    </section>
  );
}
