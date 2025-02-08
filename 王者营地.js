const axios = require('axios');
const notify = require('./sendNotify');

async function main() {
  try {
    // 从环境变量中获取Token和Body
    const tokenEnv = process.env.WZYD_TOKEN;
    const bodyEnv = process.env.WZYD_BODY;

    if (!tokenEnv || !bodyEnv) {
      console.error("环境变量 WZYD_TOKEN 或 WZYD_BODY 未设置");
      return;
    }

    const tokens = tokenEnv.split(';');
    const bodies = bodyEnv.split(';');

    if (tokens.length !== bodies.length) {
      console.error("WZYD_TOKEN 和 WZYD_BODY 数量不匹配");
      return;
    }

    const promises = tokens.map(async (token, index) => {
      try {
        const headers = JSON.parse(token);
        const payload = JSON.parse(bodies[index]);

        const response = await axios.post(
          'https://kohcamp.qq.com/operation/action/signin',
          payload,
          { headers }
        );

        console.log(`${payload.roleId} 的王者营地签到结果:`, response.data);
        await notify.sendNotify(
          `${payload.roleId} 的王者营地签到结果`,
          JSON.stringify(response.data)
        );
      } catch (error) {
        console.error(`账号 ${index + 1} 签到失败:`, error.message);
      }
    });

    await Promise.all(promises);
  } catch (error) {
    console.error("脚本运行出错:", error.message);
  }
}

main();
