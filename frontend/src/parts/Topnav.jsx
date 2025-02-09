import React from 'react';

const Topnav = () => {
    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <img src="src/assets/stonks.png" alt="Stonks" style={{ marginRight: '10px', height: '10rem' }} />
            <h2 className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-8xl" style={{ fontFamily: 'Comic Sans MS, Comic Sans' }}>
                Moonshot
            </h2>
        </div>
    );
};

export default Topnav;