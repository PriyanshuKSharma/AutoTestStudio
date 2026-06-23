import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || `${window.location.protocol}//${window.location.hostname}:8000`;
const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000/ws`;

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState({
    soc: 80.0,
    voltage: 374.4,
    current: -5.0,
    temp_max: 28.5,
    temp_min: 27.5,
    temp_avg: 28.0,
    state: 'Ready',
    faults: [],
    msg_rate: 0
  });

  const [trace, setTrace] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [filterText, setFilterText] = useState('');
  
  // History lists for charting
  const [voltageHistory, setVoltageHistory] = useState([]);
  const [currentHistory, setCurrentHistory] = useState([]);
  const [socHistory, setSocHistory] = useState([]);
  const [tempHistory, setTempHistory] = useState([]);

  // Automation / Event State
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Webhooks
  const [webhooks, setWebhooks] = useState([]);
  const [webhookName, setWebhookName] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');

  // Refs for tracking lists and websockets
  const wsRef = useRef(null);
  const traceEndRef = useRef(null);
  const isPausedRef = useRef(false);
  const reconnectTimerRef = useRef(null);
  const shouldReconnectRef = useRef(true);

  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);

  // 1. Establish WebSocket Connection
  useEffect(() => {
    connectWebSocket();
    fetchEvents();
    fetchWebhooks();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    console.log('Connecting to simulator websocket:', WS_URL);
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connection established.');
    };

    ws.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch (err) {
        console.error('Invalid websocket payload:', err);
        return;
      }
      if (payload.type === 'init') {
        const { trace_history, metrics: initMetrics } = payload.data;
        if (trace_history) setTrace(trace_history);
        if (initMetrics) {
          setMetrics(initMetrics);
          seedHistories(initMetrics);
        }
      } else if (payload.type === 'trace') {
        if (!isPausedRef.current) {
          setTrace((prev) => {
            const next = [...prev, payload.data];
            return next.slice(-200); // Limit to last 200 items in UI
          });
        }
      } else if (payload.type === 'metrics') {
        setMetrics(payload.data);
        updateHistories(payload.data);
      } else if (payload.type === 'event') {
        // Refresh event logs
        fetchEvents();
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (shouldReconnectRef.current) {
        console.log('WebSocket disconnected. Reconnecting in 3s...');
        reconnectTimerRef.current = setTimeout(connectWebSocket, 3000);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };
  };

  // Seed history lists on init
  const seedHistories = (m) => {
    setVoltageHistory(new Array(30).fill(m.voltage));
    setCurrentHistory(new Array(30).fill(m.current));
    setSocHistory(new Array(30).fill(m.soc));
    setTempHistory(new Array(30).fill(m.temp_avg));
  };

  // Append new telemetry to charts
  const updateHistories = (m) => {
    setVoltageHistory((prev) => [...prev.slice(-49), m.voltage]);
    setCurrentHistory((prev) => [...prev.slice(-49), m.current]);
    setSocHistory((prev) => [...prev.slice(-49), m.soc]);
    setTempHistory((prev) => [...prev.slice(-49), m.temp_avg]);
  };

  // 2. HTTP API Operations
  const fetchEvents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/events`);
      const data = await res.json();
      setEvents(data);
    } catch (e) {
      console.error('Error fetching events:', e);
    }
  };

  const fetchWebhooks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/webhooks`);
      const data = await res.json();
      setWebhooks(data);
    } catch (e) {
      console.error('Error fetching webhooks:', e);
    }
  };

  const injectFault = async (faultType) => {
    try {
      await fetch(`${API_BASE}/api/faults/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: faultType })
      });
      fetchEvents();
    } catch (e) {
      console.error('Error injecting fault:', e);
    }
  };

  const registerWebhook = async (e) => {
    e.preventDefault();
    if (!webhookName || !webhookUrl) return;
    try {
      const res = await fetch(`${API_BASE}/api/webhooks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: webhookName, url: webhookUrl })
      });
      if (res.ok) {
        setWebhookName('');
        setWebhookUrl('');
        fetchWebhooks();
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to register webhook');
      }
    } catch (err) {
      console.error('Error creating webhook:', err);
    }
  };

  const deleteWebhook = async (id) => {
    try {
      await fetch(`${API_BASE}/api/webhooks/${id}`, { method: 'DELETE' });
      fetchWebhooks();
    } catch (e) {
      console.error('Error deleting webhook:', e);
    }
  };

  const runAiAnalysis = async (eventId, e) => {
    if (e) e.stopPropagation();
    setSelectedEventId(eventId);
    setAiAnalysis('');
    setIsAnalyzing(true);

    try {
      const res = await fetch(`${API_BASE}/api/analyze/${eventId}`, { method: 'POST' });
      const data = await res.json();
      setIsAnalyzing(false);
      animateTypewriter(data.analysis);
    } catch (err) {
      console.error('Error running diagnostics:', err);
      setIsAnalyzing(false);
      setAiAnalysis('Error contacting AI Diagnostic service.');
    }
  };

  const animateTypewriter = (text) => {
    let index = 0;
    setAiAnalysis('');
    const timer = setInterval(() => {
      setAiAnalysis((prev) => prev + text.charAt(index));
      index++;
      if (index >= text.length) {
        clearInterval(timer);
      }
    }, 12);
  };

  // Scroll to trace bottom helper
  useEffect(() => {
    if (traceEndRef.current && !isPaused) {
      traceEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [trace, isPaused]);

  // 3. Helper math for drawing custom SVG charts
  const makeSvgPath = (data, minVal, maxVal, width = 380, height = 70) => {
    if (!data || data.length < 2) return '';
    const range = maxVal - minVal || 1;
    const padding = 4;
    const step = (width - 2 * padding) / (data.length - 1);
    
    const points = data.map((val, i) => {
      const x = padding + i * step;
      // Invert Y axis for screen space
      const y = height - padding - ((val - minVal) / range) * (height - 2 * padding);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    
    return `M ${points.join(' L ')}`;
  };

  // Determine if trace row has errors/warnings
  const getTraceRowClass = (entry) => {
    const errorFlags = entry.signals?.BMS_ErrorFlags;
    if (errorFlags && errorFlags > 0) {
      return 'trace-row row-error';
    }
    const state = entry.signals?.BMS_State;
    if (state === 'Fault') {
      return 'trace-row row-error';
    }
    if (entry.signals?.BMS_MaxCellTemp > 50) {
      return 'trace-row row-warn';
    }
    return 'trace-row';
  };

  // Filter trace messages
  const filteredTrace = trace.filter((t) => {
    if (!filterText) return true;
    const term = filterText.toLowerCase();
    return (
      t.name.toLowerCase().includes(term) ||
      t.id.toLowerCase().includes(term) ||
      t.payload.toLowerCase().includes(term)
    );
  });

  return (
    <div className="app-container">
      {/* 1. HEADER */}
      <header className="dashboard-header">
        <div className="header-brand">
          <div className="brand-logo">CAN</div>
          <div className="brand-title">
            <h1>BMS DIGITAL TWIN</h1>
            <span>Virtual CANoe Simulator Platform</span>
          </div>
        </div>
        
        <div className="header-status">
          <div className="status-item">
            <span className="status-label">Bus Status</span>
            <span className={`status-val ${isConnected ? 'online' : 'offline'}`}>
              <span className="pulse-indicator" />
              {isConnected ? 'ONLINE (vcan0)' : 'CONNECTING'}
            </span>
          </div>
          
          <div className="status-item">
            <span className="status-label">BMS Operational Mode</span>
            <span className="status-val" style={{ 
              color: metrics.state === 'Fault' ? 'var(--color-error)' : 
                     metrics.state === 'Charging' ? 'var(--color-primary)' : 'var(--color-success)'
            }}>
              {metrics.state.toUpperCase()}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">Bus Load</span>
            <span className="status-val">{metrics.msg_rate} msg/s</span>
          </div>
        </div>
      </header>

      {/* 2. MAIN WORKSPACE GRID */}
      <div className="dashboard-grid">
        
        {/* LEFT COLUMN: LIVE CAN TRACE */}
        <section className="panel">
          <header className="panel-header">
            <div className="panel-title">
              <span className="section-mark">CAN</span> Live CAN Bus Trace Window
            </div>
            <div className="panel-actions">
              <input
                type="text"
                placeholder="Filter (ID, Name)..."
                className="trace-filter-input"
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
              />
              <button 
                className={`btn ${isPaused ? 'btn-primary' : ''}`}
                onClick={() => setIsPaused(!isPaused)}
              >
                {isPaused ? 'Resume' : 'Pause'}
              </button>
              <button className="btn" onClick={() => setTrace([])}>
                Clear
              </button>
            </div>
          </header>

          <div className="trace-container">
            <table className="trace-table">
              <thead>
                <tr>
                  <th style={{ width: '12%' }}>Time (s)</th>
                  <th style={{ width: '10%' }}>ID</th>
                  <th style={{ width: '18%' }}>Name</th>
                  <th style={{ width: '8%' }}>DLC</th>
                  <th style={{ width: '22%' }}>Data (Hex)</th>
                  <th style={{ width: '30%' }}>Decoded Signals</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrace.map((t, idx) => (
                  <tr key={idx} className={getTraceRowClass(t)}>
                    <td>{t.time}</td>
                    <td>{t.id}</td>
                    <td style={{ fontWeight: 600 }}>{t.name}</td>
                    <td>{t.dlc}</td>
                    <td style={{ letterSpacing: '0.5px' }}>{t.payload}</td>
                    <td>
                      {Object.entries(t.signals || {})
                        .map(([k, v]) => `${k.replace('BMS_', '')}=${v}`)
                        .join(' | ')}
                    </td>
                  </tr>
                ))}
                <tr ref={traceEndRef} />
              </tbody>
            </table>
          </div>
        </section>

        {/* RIGHT COLUMN: TELEMETRY & CONTROLS */}
        <div className="right-column">
          
          {/* A. DASHBOARD CARD (NUMERICS) */}
          <section className="panel">
            <header className="panel-header">
              <div className="panel-title"><span className="section-mark">BMS</span> Battery Telemetry Indicators</div>
            </header>
            
            <div className="telemetry-grid">
              <div className="telemetry-card">
                <div className="card-icon-container" style={{ color: 'var(--color-primary)' }}>SOC</div>
                <div className="telemetry-meta">
                  <span className="telemetry-label">State of Charge</span>
                  <span className="telemetry-value" style={{ color: 'var(--color-primary)' }}>{metrics.soc}%</span>
                </div>
              </div>
              
              <div className="telemetry-card">
                <div className="card-icon-container" style={{ color: 'var(--color-success)' }}>V</div>
                <div className="telemetry-meta">
                  <span className="telemetry-label">Pack Voltage</span>
                  <span className="telemetry-value">{metrics.voltage} V</span>
                </div>
              </div>
              
              <div className="telemetry-card">
                <div className="card-icon-container" style={{ color: 'var(--color-secondary)' }}>A</div>
                <div className="telemetry-meta">
                  <span className="telemetry-label">Pack Current</span>
                  <span className="telemetry-value" style={{ 
                    color: metrics.current < 0 ? 'var(--color-warning)' : 
                           metrics.current > 0.5 ? 'var(--color-success)' : 'inherit'
                  }}>
                    {metrics.current} A
                  </span>
                </div>
              </div>

              <div className="telemetry-card">
                <div className="card-icon-container" style={{ color: 'var(--color-error)' }}>C</div>
                <div className="telemetry-meta">
                  <span className="telemetry-label">Max Cell Temp</span>
                  <span className="telemetry-value" style={{ 
                    color: metrics.temp_max > 55 ? 'var(--color-error)' : 'inherit'
                  }}>
                    {metrics.temp_max} °C
                  </span>
                </div>
              </div>
            </div>

            {/* RADIAL DIALS */}
            <div className="gauge-section">
              <div className="gauge-wrapper">
                <svg className="gauge-svg">
                  <circle className="gauge-bg" cx="45" cy="45" r="36" />
                  <circle 
                    className="gauge-fill primary" 
                    cx="45" cy="45" r="36" 
                    strokeDasharray={2 * Math.PI * 36}
                    strokeDashoffset={2 * Math.PI * 36 * (1 - metrics.soc / 100)}
                  />
                </svg>
                <div className="gauge-text">
                  <span className="gauge-val">{metrics.soc}%</span>
                  <span className="gauge-lbl">SOC</span>
                </div>
              </div>

              <div className="gauge-wrapper">
                <svg className="gauge-svg">
                  <circle className="gauge-bg" cx="45" cy="45" r="36" />
                  <circle 
                    className={`gauge-fill ${metrics.temp_max > 55 ? 'error' : metrics.temp_max > 40 ? 'warn' : 'success'}`} 
                    cx="45" cy="45" r="36" 
                    strokeDasharray={2 * Math.PI * 36}
                    strokeDashoffset={2 * Math.PI * 36 * (1 - Math.min(100, Math.max(0, metrics.temp_max + 40)) / 140)}
                  />
                </svg>
                <div className="gauge-text">
                  <span className="gauge-val">{metrics.temp_max}°C</span>
                  <span className="gauge-lbl">TEMP</span>
                </div>
              </div>
            </div>

            {/* MINI HISTORICAL CHARTS */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="chart-container">
                <span className="chart-badge">VOLTAGE (V)</span>
                <svg className="chart-svg">
                  <line x1="0" y1="35" x2="380" y2="35" className="chart-grid" strokeDasharray="3 3" />
                  <path 
                    className="chart-line" 
                    d={makeSvgPath(voltageHistory, 250, 430)} 
                    style={{ stroke: 'var(--color-success)' }}
                  />
                </svg>
              </div>

              <div className="chart-container">
                <span className="chart-badge">CURRENT (A)</span>
                <svg className="chart-svg">
                  <line x1="0" y1="35" x2="380" y2="35" className="chart-grid" strokeDasharray="3 3" />
                  <path 
                    className="chart-line" 
                    d={makeSvgPath(currentHistory, -100, 50)} 
                    style={{ stroke: 'var(--color-secondary)' }}
                  />
                </svg>
              </div>
            </div>
          </section>

          {/* B. FAULT INJECTION CONTROLS */}
          <section className="panel">
            <header className="panel-header">
              <div className="panel-title"><span className="section-mark">DTC</span> Diagnostic Fault Injection Panel</div>
            </header>
            <div className="fault-grid">
              <button 
                className="btn btn-danger btn-fault"
                onClick={() => injectFault('over_voltage')}
              >
                Inject Over-Voltage
              </button>
              <button 
                className="btn btn-danger btn-fault"
                onClick={() => injectFault('under_voltage')}
              >
                Inject Under-Voltage
              </button>
              <button 
                className="btn btn-danger btn-fault"
                onClick={() => injectFault('over_temperature')}
              >
                Inject Over-Temp
              </button>
              <button 
                className="btn btn-success btn-fault"
                onClick={() => injectFault('clear')}
              >
                Clear Active Faults
              </button>
            </div>
          </section>

          {/* C. AI ANALYSIS & AUTOMATION */}
          <section className="panel ai-automation-section">
            <header className="panel-header">
              <div className="panel-title"><span className="section-mark">AI</span> Defect Diagnostics & n8n Hub</div>
            </header>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minHeight: 0 }}>
              <span className="telemetry-label">Select Fault Log Event to Analyze</span>
              <div className="events-list">
                {events.length === 0 ? (
                  <div style={{ padding: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
                    No simulation events logged yet. Trigger faults to log events.
                  </div>
                ) : (
                  events.map((e) => (
                    <div 
                      key={e.id}
                      className={`event-item ${selectedEventId === e.id ? 'active' : ''}`}
                      onClick={() => runAiAnalysis(e.id)}
                    >
                      <span className={`event-badge ${
                        e.severity === 'ERROR' ? 'error' : e.severity === 'WARNING' ? 'warning' : 'info'
                      }`}>
                        {e.event_type.replace('_', ' ')}
                      </span>
                      <div className="event-meta">
                        <span className="event-title">{e.message}</span>
                        <span className="event-time">{new Date(e.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <button className="btn btn-primary" style={{ padding: '2px 8px', fontSize: '10px' }}>
                        Analyze
                      </button>
                    </div>
                  ))
                )}
              </div>

              <div className="analysis-result-box">
                <h3>Diagnostics Agent Analysis</h3>
                {isAnalyzing ? (
                  <div style={{ color: 'var(--color-primary)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className="pulse-indicator" style={{ color: 'var(--color-primary)' }} />
                    Running LLM Diagnostic Inference Models...
                  </div>
                ) : aiAnalysis ? (
                  <div className="analysis-text">{aiAnalysis}</div>
                ) : (
                  <span style={{ color: 'var(--text-muted)' }}>
                    Select an event above or click "Analyze" to inspect root cause diagnostics.
                  </span>
                )}
              </div>

              {/* Webhook Configuration */}
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '8px' }}>
                <span className="telemetry-label">Configure Webhooks (n8n integration)</span>
                <form onSubmit={registerWebhook} className="webhook-form">
                  <input
                    type="text"
                    placeholder="Name (e.g. n8n local)"
                    className="webhook-input"
                    value={webhookName}
                    onChange={(e) => setWebhookName(e.target.value)}
                  />
                  <input
                    type="url"
                    placeholder="http://localhost:5678/webhook/..."
                    className="webhook-input"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                  />
                  <button type="submit" className="btn btn-success">Add Link</button>
                </form>

                <div className="webhook-list">
                  {webhooks.map((w) => (
                    <div key={w.id} className="webhook-item">
                      <strong style={{ color: 'var(--color-primary)' }}>{w.name}</strong>
                      <span className="webhook-url">{w.url}</span>
                      <button 
                        className="btn btn-danger" 
                        style={{ padding: '1px 6px', fontSize: '9px' }}
                        onClick={() => deleteWebhook(w.id)}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
