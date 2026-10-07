import React, { createContext, useContext, useState, useEffect } from 'react';

const FolliCareContext = createContext();

export function FolliCareProvider({ children }) {
  const [theme, setTheme] = useState('botanical-emerald');
  const [cart, setCart] = useState([]);
  const [isDevMode, setIsDevMode] = useState(false);
  const [products, setProducts] = useState([]);
  const [activeBanner, setActiveBanner] = useState({
    message: '🌿 Clinical Botanical Formulation • 60-Day Satisfaction Guarantee',
    code: 'BOTANICAL20'
  });
  const [heroContent, setHeroContent] = useState({
    title: 'Botanical Precision. Clinical Hair Density.',
    subtitle: 'Formulated with active peptides, cold-pressed botanical extracts, and clean biomimetic actives to restore scalp vitality.'
  });
  const [telemetry, setTelemetry] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => {
        if (data.products) setProducts(data.products);
      })
      .catch(err => console.error('Failed to fetch products:', err));
  }, []);

  const addToCart = (product, quantity = 1) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, quantity: item.quantity + quantity } : item);
      }
      return [...prev, { ...product, quantity }];
    });
  };

  const removeFromCart = (id) => {
    setCart(prev => prev.filter(item => item.id !== id));
  };

  const [cardStyles, setCardStyles] = useState({});
  const [activeProduct, setActiveProduct] = useState(null);

  const updateProductPrice = (productIdentifier, newPrice) => {
    setProducts(prev => prev.map(p => {
      const match = p.id === productIdentifier || p.name.toLowerCase().includes(productIdentifier.toLowerCase());
      return match ? { ...p, price: parseFloat(newPrice) } : p;
    }));
  };

  const updateCardStyle = (target, styleConfig) => {
    setCardStyles(prev => ({
      ...prev,
      [target.toLowerCase()]: {
        ...prev[target.toLowerCase()],
        ...styleConfig
      }
    }));
  };

  const executeUICommand = (cmd) => {
    const action = cmd.action;
    const payload = cmd.payload || {};
    if (action === 'SET_THEME') {
      setTheme(cmd.theme || payload.theme);
    } else if (action === 'SET_BANNER') {
      setActiveBanner({
        message: cmd.message || payload.message,
        code: cmd.code || payload.code
      });
    } else if (action === 'UPDATE_HERO') {
      setHeroContent({
        title: cmd.title || payload.title || heroContent.title,
        subtitle: cmd.subtitle || payload.subtitle || heroContent.subtitle
      });
    } else if (action === 'ADD_TO_CART') {
      const pName = cmd.productName || payload.productName;
      const qty = cmd.quantity || payload.quantity || 1;
      const matched = products.find(p => p.name.toLowerCase().includes((pName || '').toLowerCase()));
      if (matched) addToCart(matched, qty);
    } else if (action === 'UPDATE_PRODUCT_PRICE') {
      const pName = payload.productName || cmd.productName;
      const nPrice = payload.newPrice || cmd.newPrice;
      if (pName && nPrice) updateProductPrice(pName, nPrice);
    } else if (action === 'UPDATE_CARD_STYLE') {
      const target = payload.target || cmd.target || 'all';
      updateCardStyle(target, payload);
    }
  };

  return (
    <FolliCareContext.Provider value={{
      theme, setTheme,
      cart, addToCart, removeFromCart,
      isDevMode, setIsDevMode,
      products, setProducts, updateProductPrice,
      cardStyles, updateCardStyle,
      activeProduct, setActiveProduct,
      activeBanner, setActiveBanner,
      heroContent, setHeroContent,
      telemetry, setTelemetry,
      executeUICommand
    }}>
      {children}
    </FolliCareContext.Provider>
  );
}

export function useFolliCare() {
  return useContext(FolliCareContext);
}
