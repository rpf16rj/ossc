# Spec 003 — IT6613: áudio, AV mute e dead code

## Contexto

O driver IT6613 tem uma "camada intermediária" inteira morta: `init_it`,
`HDMITX_DevLoopProc`, `CheckHDMITX` (HPD/RxSense/DDC recovery), parser de EDID
do sink, `SetupAudioChannel`/`AutoAdjustAudio` (recovery de `B_OSF_LOCK`),
`SetNCTS`, HDCP (~1200 linhas), `Get6613Reg` (dump de regs pronto). Nada disso
é chamado. Issues de áudio (#26, #34) mapeiam em mecanismos que existem mas não
rodam: se o clock de oversampling de áudio perde lock (`B_OSF_LOCK`, reg 0x5F
bit5) ou `REG_TX_AUD_SRCVALID_FLAT` (0xE4, `B_AUD_ERR2FLAT`) trava o áudio, nada
re-arma até o próximo `TX_enable` completo.

## Requisitos

- `[FW]` ✅ ITU709 no AVI infoframe (feito no P0 — derivado de timings de saída).
- `[FW]` Poll leve no `get_status()`/mainloop: checar OSF_LOCK e re-escrever
  `REG_TX_AUDIO_CTRL0` + limpar flag flat quando necessário. Meta: áudio se
  recupera sozinho de glitch de TMDS sem troca de modo.
- `[FW]` Opção "audio compat": forçar `audio_dw_sampl`/N-CTS conservadores e/ou
  implementar caminho `MANUAL_CTS` corretamente (código ifdef existe mas
  `MANUAL_CTS` não é definido e tem bug ×1000 em `it6613_drv.c` ~531).
- `[FW]` Expor TMDS swing/pre-emphasis: `REG_TX_AFE_ISW_CTRL` 0x63 (hoje fixo
  0x10), `REG_TX_AFE_RING` 0x65, `REG_TX_AFE_TEST` 0x66 — fix clássico para
  sparkle/dropout em cabos marginais.
- `[FW]` Reduzir latência mute→unmute: `DelayMS(100)` fixo + poll VIDSTABLE
  (~200ms) em `SetupAFE`/`EnableVideoOutput` — reordenar poll para antes do delay
  ou pular AFE quando só o nível muda.
- `[FW]` Opcional: `SetSPDInfoFrame` com "OSSC" (cosmético, grátis).
- `[FW]` Poda de dead code (~2500+ linhas): `it6613.c` inteiro, `it6613_sys.c`,
  HDCP block, DEGEN/SyncEmb tables, `EnableAudioOutput` genérico. Manter sob
  `#ifdef` ou remover — decidir no diff.
- `[FW]` Usar `Get6613Reg` para endpoint/função de dump de registradores (debug).
- Documentar: #97 (áudio em modo DVI) não é viável — DVI não tem data islands;
  sugerir modo "HDMI vídeo+áudio, AVI rotulado DVI" só se houver demanda real.

## Abordagem técnica

- Recovery de áudio: função `hdmitx_audio_healthcheck()` chamada 1x por loop quando
  `cm.cc.tx_mode != TX_DVI`; ler 0x5F/0xE4, re-armar se flag set. Custo: 2 leituras
  I2C por iteração (~10ms) — aceitável, ou apenas a cada ~500ms.
- Campos novos em `avconfig_t` (tmds_swing etc.) + itens UDE ver 123.
- Remover dead code em commit separado para facilitar upstream review.

## Critérios de aceite

- Áudio volta sozinho após perda simulada de lock (teste em HW).
- Latência mute→unmute medida antes/depois (JTAG printf timestamp).
- Sem regressão: TX_enable continua produzindo imagem/áudio em todos tx_mode.

## Referências

- `it6613_drv.c` (~297 InitIT6613, ~419-435 VIDSTABLE/SetupAFE, ~527
  EnableAudioOutput4OSSC, ~547 MANUAL_CTS ifdef, ~576 AUD_ERR2FLAT, ~857 GCP,
  ~887 Get6613Reg, ~1559 DelayMS, ~1720-1853 SetupAudioChannel/AutoAdjustAudio,
  ~2179-3200 HDCP)
- `HDMI_TX.c` (~81 SetAVIInfoFrame, ~330 audio infoframe), `it6613.c` (morto),
  `it6613_sys.c`, `EDID.c` (parser morto — pode virar "sink caps" no futuro)
- Upstream issues #26, #34, #97, #125
