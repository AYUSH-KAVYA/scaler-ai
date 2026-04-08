class NeonGridUI {
    constructor() {
        this.currentState = null;
        this.autoplayInterval = null;
        
        // Element bindings
        this.btnReset = document.getElementById('btn-reset');
        this.btnStep = document.getElementById('btn-step');
        this.btnAutoplay = document.getElementById('btn-autoplay');
        this.btnTransmit = document.getElementById('btn-transmit');
        this.inputCommand = document.getElementById('input-command');
        this.taskSelect = document.getElementById('task-select');
        this.terminal = document.getElementById('terminal-log');
        
        this.init();
    }

    init() {
        this.btnReset.addEventListener('click', () => this.resetEnv());
        this.btnStep.addEventListener('click', () => this.stepEnv());
        this.btnAutoplay.addEventListener('click', () => this.toggleAutoplay());
        this.btnTransmit.addEventListener('click', () => this.sendCommand());
        this.inputCommand.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCommand();
        });
        
        // Mode toggles
        document.querySelectorAll('.tri-toggle button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const parent = e.target.parentElement;
                parent.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    log(msg) {
        const div = document.createElement('div');
        div.textContent = `> ${msg}`;
        this.terminal.appendChild(div);
        this.terminal.scrollTop = this.terminal.scrollHeight;
    }

    async resetEnv() {
        const difficulty = this.taskSelect.value;
        this.log(`INITIALIZING GRID CORE [TASK: ${difficulty.toUpperCase()}]...`);
        
        try {
            // OpenEnv Standard POST /reset
            const response = await fetch('/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const data = await response.json();
            // OpenEnv returns {observation: {...}, reward: ..., done: ...}
            this.updateUI(data.observation, data.reward);
            this.log("READY. SYSTEM STABLE.");
        } catch (err) {
            console.error(err);
            this.log(`ERROR: GRID CONNECTION FAILED [${err.message || 'NET_ERROR'}]`);
        }
    }

    async stepEnv() {
        if (this.currentState && this.currentState.done) return;
        
        const consumption = document.querySelector('#toggle-consumption .active').dataset.val;
        const battery = document.querySelector('#toggle-battery .active').dataset.val;
        
        try {
            // OpenEnv Standard POST /step with {action: {...}}
            const response = await fetch('/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: {
                        consumption_mode: consumption,
                        battery_mode: battery,
                        source_priority: 'solar'
                    }
                })
            });
            const data = await response.json();
            // OpenEnv returns {observation: {...}, reward: ..., done: ...}
            const obs = data.observation;
            obs.done = data.done;
            this.updateUI(obs, data.reward);
            this.log(obs.status_message);
        } catch (err) {
            console.error(err);
            this.log(`ERROR: SYNC LOST [${err.message || 'NET_ERROR'}]`);
            setTimeout(() => this.log("ATTEMPTING RE-SYNCHRONIZATION..."), 2000);
        }
    }

    updateUI(obs, reward) {
        this.currentState = obs;
        if (reward !== undefined) this.currentState.reward = reward;
        
        // Labels
        document.getElementById('label-time').textContent = obs.current_time;
        document.getElementById('label-weather').textContent = obs.weather.toUpperCase();
        
        // Metrics
        document.getElementById('val-comfort').textContent = `${Math.round(obs.comfort_index * 100)}%`;
        document.getElementById('bar-comfort').style.width = `${obs.comfort_index * 100}%`;
        
        document.getElementById('val-battery').textContent = `${Math.round(obs.battery_level)}%`;
        document.getElementById('bar-battery').style.width = `${obs.battery_level}%`;
        
        document.getElementById('val-price').textContent = `$${obs.grid_price.toFixed(2)}`;
        document.getElementById('val-demand').textContent = `${obs.district_demand.toFixed(1)} MW`;
        
        // Use the reward passed in, or fallback to the one in state
        const rewardVal = reward !== undefined ? reward : (obs.reward || 0);
        document.getElementById('val-reward').textContent = rewardVal.toFixed(2);
        
        // Visual flow intensity
        const solarOpacity = obs.solar_output > 0 ? 1 : 0.2;
        document.getElementById('flow-solar').style.opacity = solarOpacity;
    }

    toggleAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
            this.btnAutoplay.textContent = "CORE AUTO-PILOT";
            this.btnAutoplay.classList.remove('active-flash');
        } else {
            this.log("STARTING AI ARCHITECT AUTO-SIMULATION...");
            this.btnAutoplay.textContent = "STOP AUTO-PILOT";
            this.btnAutoplay.classList.add('active-flash');
            this.autoplayInterval = setInterval(() => {
                if (this.currentState && this.currentState.done) {
                    this.toggleAutoplay();
                    return;
                }
                this.aiStep();
            }, 1000);
        }
    }

    async sendCommand() {
        const cmd = this.inputCommand.value.trim();
        if (!cmd) return;
        
        this.log(`TRANSMITTING DIRECTIVE: "${cmd.toUpperCase()}"`);
        this.inputCommand.value = "";
        
        try {
            await fetch('/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ directive: cmd })
            });
            this.log("DIRECTIVE UPLOAD COMPLETE. ARCHITECT SYNCHRONIZED.");
        } catch (err) {
            this.log("ERROR: UPLOAD FAILED.");
        }
    }

    aiStep() {
        // Simple heuristic agent for visual show
        const batteryToggle = document.getElementById('toggle-battery');
        const consToggle = document.getElementById('toggle-consumption');
        
        // Logic: If price is high, discharge. If low & battery < 100, charge.
        if (this.currentState.grid_price >= 0.3) {
            batteryToggle.querySelector('[data-val="discharge"]').click();
            consToggle.querySelector('[data-val="low"]').click();
        } else {
            batteryToggle.querySelector('[data-val="charge"]').click();
            consToggle.querySelector('[data-val="normal"]').click();
        }
        
        this.stepEnv();
    }
}

// Start on load
window.addEventListener('DOMContentLoaded', () => {
    new NeonGridUI();
});
