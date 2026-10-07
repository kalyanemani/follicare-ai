import React, { useState } from 'react';
import { useFolliCare } from '../context/FolliCareContext';
import { useCopilotReadable, useCopilotAction } from './CopilotKitIntegration';

export function ProductCard({ product }) {
  const { addToCart, cardStyles, updateProductPrice, updateCardStyle, setActiveProduct } = useFolliCare();
  
  // Calculate dynamic style overrides for this product card
  const prodKey = (product.name || '').toLowerCase();
  const isTargeted = Object.keys(cardStyles).some(k => prodKey.includes(k));
  const activeStyle = Object.entries(cardStyles).find(([k]) => prodKey.includes(k))?.[1] || cardStyles['all'] || {};

  const cardScale = activeStyle.scale || 1.0;
  const cardMaxWidth = activeStyle.maxWidth || '100%';
  const cardPadding = activeStyle.padding || '24px';

  // 1. Expose this product card to CopilotKit LLM
  useCopilotReadable({
    description: `Product Card: ${product.name} (Price: $${product.price})`,
    value: {
      id: product.id,
      name: product.name,
      price: product.price,
      hairConcern: product.hairConcern,
      activeIngredients: product.activeIngredients,
      layout: { scale: cardScale, maxWidth: cardMaxWidth, padding: cardPadding }
    }
  });

  // 2. Allow Copilot to resize this specific card
  useCopilotAction({
    name: `resizeCard_${product.id}`,
    description: `Resize product card for ${product.name}`,
    parameters: [
      { name: "maxWidth", type: "string", description: "e.g. '220px' or '300px'" },
      { name: "scale", type: "number", description: "Scale multiplier between 0.75 and 1.25" }
    ],
    handler: ({ maxWidth, scale }) => {
      updateCardStyle(product.name, { maxWidth: maxWidth || '220px', scale: scale || 0.88 });
      return `Successfully resized ${product.name} card.`;
    }
  });

  // 3. Allow Copilot to update price
  useCopilotAction({
    name: `updatePrice_${product.id}`,
    description: `Update the price for ${product.name}`,
    parameters: [
      { name: "newPrice", type: "number", description: "New price in USD" }
    ],
    handler: ({ newPrice }) => {
      updateProductPrice(product.id, newPrice);
      return `Updated price of ${product.name} to $${newPrice}`;
    }
  });

  return (
    <div
      onMouseEnter={() => setActiveProduct(product)}
      style={{
        background: 'var(--bg-card)', backdropFilter: 'blur(12px)',
        border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)',
        padding: cardPadding, display: 'flex', flexDirection: 'column',
        position: 'relative', overflow: 'hidden',
        maxWidth: cardMaxWidth,
        transform: `scale(${cardScale})`,
        transformOrigin: 'top center',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        boxShadow: isTargeted ? '0 0 20px rgba(16, 185, 129, 0.25)' : 'none'
      }}
    >
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
          ${parseFloat(product.price).toFixed(2)}
        </div>
        <button
          onClick={() => addToCart(product, 1)}
          style={{
            background: 'var(--accent-color)', color: '#ffffff', border: 'none',
            padding: '8px 16px', borderRadius: 'var(--radius-md)', fontWeight: 700,
            cursor: 'pointer', transition: 'all 0.2s ease'
          }}
        >
          Add to Bag
        </button>
      </div>
    </div>
  );
}

export function ProductCatalog() {
  const { products, setTheme } = useFolliCare();
  const [filter, setFilter] = useState('All');

  // Register catalog filtering action for CopilotKit
  useCopilotAction({
    name: "filterCatalogByConcern",
    description: "Filter storefront catalog by concern or category",
    parameters: [
      { name: "category", type: "string", description: "'All', 'Scalp Care', 'Shampoo', 'Treatments', 'Hair Fall'" }
    ],
    handler: ({ category }) => {
      setFilter(category);
      return `Filtered catalog by ${category}`;
    }
  });

  // Register theme changer action
  useCopilotAction({
    name: "changeStoreTheme",
    description: "Switch storefront color palette (botanical-emerald, ruby-red, velvet-lavender, royal-amber)",
    parameters: [
      { name: "themeName", type: "string", description: "Target theme name" }
    ],
    handler: ({ themeName }) => {
      setTheme(themeName);
      return `Switched storefront theme to ${themeName}`;
    }
  });

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
              borderRadius: '9999px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '24px', alignItems: 'start'
      }}>
        {filtered.map(prod => (
          <ProductCard key={prod.id} product={prod} />
        ))}
      </div>
    </section>
  );
}
