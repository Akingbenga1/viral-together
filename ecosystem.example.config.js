module.exports = {
  apps: [{
    name: 'viral-together',
    script: 'gunicorn',
    args: 'app.main:app --config gunicorn.conf.py',
    interpreter: '/root/projects/viral-together/********/bin/python',
    cwd: '/root/projects/viral-together',
    env: {
      PYTHONPATH: '/root/projects/viral-together',
      VIRTUAL_ENV: '/root/projects/viral-together/*********',
      PATH: '/root/projects/viral-together/*******/bin:' + process.env.PATH,
      DATABASE_URL: 'postgresql+asyncpg://*******:******@localhost:5432/viral_together',
      ENV: 'production'
    },
    env_production: {
      PYTHONPATH: '/root/projects/viral-together',
      VIRTUAL_ENV: '/root/projects/viral-together/******',
      PATH: '/root/projects/viral-together/*******/bin:' + process.env.PATH,
      DATABASE_URL: 'postgresql+asyncpg://************:************@localhost:5432/viral_together',
      ENV: 'production'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_file: './logs/pm2-combined.log',
    time: true
  }]
};
