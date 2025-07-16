<template>
  <div class="header">
    <h1>🛡️ 四川烟草商业融媒发布合规监测平台</h1>
    <p>智能内容审核 · 多引擎融合 · 实时监控</p>
  </div>
</template>

<style scoped>
.header {
  background: linear-gradient(135deg, #c41e3a 0%, #8b1538 100%);
  color: white;
  padding: 30px;
  text-align: center;
  position: relative;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
  opacity: 0.3;
}

.header h1 {
  font-size: 2.5em;
  margin-bottom: 10px;
  position: relative;
  z-index: 1;
}

.header p {
  font-size: 1.1em;
  opacity: 0.9;
  position: relative;
  z-index: 1;
}
</style>