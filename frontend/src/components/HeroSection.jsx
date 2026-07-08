import React from 'react';

const LOCALITY_IMAGES = {
  indiranagar: {
    url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBCdq4ncRv9t5IcezOEAbjKE5WpIuR6Y1uy4TH-k-j-Ja-m8EqvJDDdqhbw_HXEW5xlIFhVKYZrk5V6WdYdqoS6DYVLtqx3TpAq-a8WO56eOu5afLFaRnZc2eSZjF8iIvK__VJjhAbnlRoB6Ij4mVVG19DrGhhCiN4IWPX1XZw_5CKlL_MDrh5XbHROK0rSk0swdvNkO75Y4J_3QjkmBrYO5OwTG1f2dejnOy2BFJIKHJxebPq8OYU',
    vibe: 'Vibe: Indiranagar Evening'
  },
  basavanagudi: {
    url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA0e3nwim6JL5WBQxHzt5WOesdNlWe5ednjvTScepIdkmduG7DaXQUIwXDFyH6ulWsr_NruatBMKJJPO0kcvkK0DwMyqSFSQOiN_B4H61Ip5C03zSOnLOr2MkS8d_v6Lrrv8dG8UAKjYFcOpIQhGm40JI919gtgTnd-dVzZJbCIXM9ICmLaiZSb6t3BZyJzf1ydShOAHOkjro-mcFtPBeZy9T4AEyuKmx6afJbWW7_j53eIsH8zZWA',
    vibe: 'Vibe: Basavanagudi Heritage Breakfast'
  },
  koramangala: {
    url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDPkuJp6fmIvMhqOM4PnYGBDzZIbTMZRulvev1wqqUNAo4bHiok3_u_XV85_hrX4eQ4nB3B5gYAyMa2NDPFwpLDmFINSyjpQElG_SC1AyJ6po1fmrceSReFr3ysJ5_ZEUkot0Kro7_oPCC9lMA9tqzrVxGA_BWZLJtsk-gHXNpxRJVWs39JjF7qMCRy2P-31QR9wZK_0WE0spXeGSj2A9sq67MMekKkICM6WoQbUA8BfljU4j96cgA',
    vibe: 'Vibe: Koramangala Cafe Alley'
  },
  hsr: {
    url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAGZGzU7K6M4dFA-EktyFtk6Qlal60Jp10E9whQvBpBD-KV8b4sYHIGo-Wp1AVisH53ttXNbuVmLxB82_IXpJ5FYb84IfkH5p8Q52jaBcLEaaxoM-IBy8iwXOjp2aVCZln9m5LWH_WiX1oLtf4oK5MVCYawv01Rn7FKL0AO1aDxGdAcLCiuVEcmveeRaw36F2hT-UjOodMGLqQgx3uD_SLStbRC0sFxEliClnXYtzg3RpmaIfOpI0s',
    vibe: 'Vibe: HSR Brewery Culture'
  },
  default: {
    url: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBCdq4ncRv9t5IcezOEAbjKE5WpIuR6Y1uy4TH-k-j-Ja-m8EqvJDDdqhbw_HXEW5xlIFhVKYZrk5V6WdYdqoS6DYVLtqx3TpAq-a8WO56eOu5afLFaRnZc2eSZjF8iIvK__VJjhAbnlRoB6Ij4mVVG19DrGhhCiN4IWPX1XZw_5CKlL_MDrh5XbHROK0rSk0swdvNkO75Y4J_3QjkmBrYO5OwTG1f2dejnOy2BFJIKHJxebPq8OYU',
    vibe: 'Vibe: Bangalore Dining Scene'
  }
};

export default function HeroSection({ selectedLocation }) {
  // Extract clean locality key
  const locKey = selectedLocation
    ? selectedLocation.toLowerCase().replace(', bangalore', '').trim()
    : 'default';

  // Get matching info or default
  const info = LOCALITY_IMAGES[locKey] || LOCALITY_IMAGES.default;

  return (
    <div className="hero-col">
      <h1 className="heading-lg">
        Personalized picks from real Zomato data — filtered by you, ranked by AI.
      </h1>
      <p className="body-lg">
        Discover the best of Bangalore's culinary scene. Tell us what you're craving, and our AI will comb through thousands of reviews to find your perfect match in Indiranagar, Jayanagar, and beyond.
      </p>
      
      <div className="locality-card">
        <img 
          src={info.url} 
          alt={info.vibe} 
          className="locality-img" 
        />
        <div className="locality-overlay">
          <span className="sparkle-badge">Contextual Sparkle</span>
          <p className="locality-vibe">{info.vibe}</p>
        </div>
      </div>
    </div>
  );
}
