const { v4: uuidv4 } = require('uuid');

async function generateECDSAKeyPair(n,t) {
    // 生成 ECDSA 密钥对，私钥设置为不可导出
    const keyPair = await crypto.subtle.generateKey(
        {
            name: "ECDSA",
            namedCurve: "P-256"
        },
        false,              // 设置 extractable 为 false
        ["sign", "verify"]  // 私钥: sign, 公钥: verify
    );


    // 公钥仍可导出
    const exportedPublicKey = await crypto.subtle.exportKey("jwk", keyPair.publicKey);
    delete exportedPublicKey.ext
    delete exportedPublicKey.key_ops
    let p = JSON.stringify({
        typ: "dpop+jwt",
        alg: "ES256",
        jwk: exportedPublicKey
    })
    console.log()
    let g = JSON.stringify({
                    iat: Math.floor(Date.now() / 1000),
                    jti: uuidv4(),
                    htu: n,
                    htm: t,
                    uuid: "07eede5c-3f3d-48fc-85b2-c11fdfe4101c"
                })

    let o = e => e.replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_")
          , a = e => o(btoa(String.fromCharCode(...new Uint8Array(e))))
    , c = e => new TextEncoder().encode(unescape(encodeURIComponent(e)))
    let m = [(0,
                a)(c(p)), (0,
                a)(c(g))].join(".")

    const data = new TextEncoder().encode(m);
    const signature = await crypto.subtle.sign(
        {name: "ECDSA", hash: {name: "SHA-256"}},
        keyPair.privateKey,
        data
    );
    console.log("".concat(m, ".").concat(a(signature)))

    return "".concat(m, ".").concat(a(signature))


}