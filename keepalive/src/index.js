/**
 * Keep-alive worker for the saga demo.
 *
 * Periodically requests a session-backed endpoint so that the API server on Koyeb
 * wakes up and issues a Redis command (a new session is created via SETEX since
 * no cookie is sent), keeping the Upstash free-tier instance from going idle.
 */

export default {
  async scheduled(controller, env, ctx) {
    const res = await fetch(env.TARGET_URL, {
      headers: { "User-Agent": "saga-demo-keepalive" },
    });

    if (!res.ok) {
      // Throwing marks the cron run as failed in the Cloudflare dashboard
      throw new Error(`Keep-alive failed: ${res.status} ${await res.text()}`);
    }

    console.log(`Keep-alive OK: ${res.status} ${env.TARGET_URL}`);
  },
};
