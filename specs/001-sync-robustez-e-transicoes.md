# Spec 001 — Robustez de sync e transições de modo

## Contexto

O frontend (`rtl/tvp7002_frontend.v`) reseta `h_cnt` e incrementa `v_cnt`/`vmax_cnt`
a **cada** borda de descida de `HS_i` (linha ~200). Não há filtro de glitch no
domínio de captura: uma borda espúria (32X, Neo Geo, crosstalk em transição
240p↔480i) adianta a contagem de linha, pode disparar `frame_change` uma linha
cedo e dessincroniza a paridade do linebuf (`linebuf_top.v` avança buffer em
qualquer mudança de `ypos_i`) → tear vertical + resync strobe.

O domínio de *medição* já tem `glitch_filt_thold`; o domínio de *amostragem* não
tem nada.

`frame_change_resync` (`scanconverter.v` ~381) reseta `h_cnt`/`v_cnt` a qualquer
`frame_change` fora da janela ±128px de `V_STARTLINE` — um único vsync tardio
produz salto de frame visível.

Issues relacionadas: #126 (Uzebox mode 3), #132 (interlaced/glitch em transição),
#135 (Sega 32X).

## Requisitos

- `[RTL]` Rejeitar borda de hsync que chegue a menos de ~1/4 de linha da anterior
  (pulsos de equalização de meia-linha ainda passam). Gatear por bit livre de
  `misc_config` (bits 25-31 livres) para habilitar por perfil.
- `[RTL]` Persistência no resync: exigir N (2) detecções consecutivas fora da
  janela antes de resetar — ou expor a janela em `hv_out_config3[31:24]` (livre).
- `[FW]` Perfil/preset "unstable sync" que ligue o filtro + alargue tolerâncias
  (`linelen_tol`, `pre_coast`/`post_coast`, `adc_pll_bw=Ultra low` — já expostos
  em menu).
- `[FW]` Double-sample dos regs `fe_status`/`fe_status2` em `get_status()` para
  evitar tupla rasgada (totlines vs pcnt_field) durante instabilidade.

## Abordagem técnica

1. No bloco clocked por `PCLK_i`: aceitar `HS_i` falling apenas se
   `h_cnt > (H_TOTAL >> 2)` quando `misc_config[25]` (novo bit `hsync_glitch_filt`)
   estiver ativo. `h_cnt` e `H_TOTAL` estão nas mesmas unidades decimadas
   (escala correta com `H_SKIP>0`).
2. `frame_change` resync: contador de 2 bits que só reseta após 2 detecções
   consecutivas fora da janela; reseta o contador ao ver frame_change dentro da
   janela.
3. Firmware: re-aplicável por perfil via novo campo `avconfig_t` (ver UDE; item
   novo é auto-compatível com perfis antigos).
4. `get_status()`: ler `fe_status` duas vezes até estabilizar (ou ler, reler e
   comparar) dentro do `STATUS_TIMEOUT_US`.

## Critérios de aceite

- Sem mudança de comportamento com bit de filtro = 0 (default).
- Com filtro ativo, pulsos < H_TOTAL/4 não avançam `v_cnt`.
- Uma única detecção fora de janela não causa resync.
- Compila no Quartus (verificar width/lint); firmware continua cabendo no BRAM.

## Referências

- `rtl/tvp7002_frontend.v` (~200, ~503), `rtl/scanconverter.v` (~381, ~459),
  `rtl/linebuf_top.v` (~263)
- `ip/sc_config/` (regs `misc_config`, `hv_out_config3`)
- Upstream issues #126, #132, #135; workaround documentado por marqs (tolerância
  hsync + ADC PLL BW ultra low) já existe — esta spec torna automático/perfil.
