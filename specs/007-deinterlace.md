# Spec 007 — Deinterlace e hooks dormentes do linebuf

## Contexto

O RTL já tem hooks de deinterlace **ligados em zero**: `MISC_LM_DEINT_MODE` e
`MISC_NIR_EVEN_OFFSET` estão hardwired a 0 (`scanconverter.v` ~157-158) apesar
de existirem no bitfield `misc_config` (7 bits livres em `sc_config_regs.h`
~115). Issue #132 (problema de imagem interlaced) e #100 (deinterlace por
interpolação de linhas adjacentes) passam por aqui.

`linebuf_top.v`: 32 buffers, uma porta de leitura `ypos_lb`. Framebuffer cheio
não existe — deinterlace motion-adaptive completo é OSSC Pro.

## Requisitos

- `[RTL+FW]` Expor `lm_deint_mode` e `nir_even_offset` nos bits livres de
  `misc_config` + campos em `avconfig_t` + menu. Ativa o caminho
  noninterlace-restore já sintetizado — primeiro degrau de #132/#100.
- `[RTL]` Deinterlace por interpolação de linha (barato): ler linha anterior em
  registrador de shift durante parte ociosa da linha de saída e média — o
  clock de leitura do linebuf é >=2x o de escrita em modos LM, há slack.
- `[RTL]` Scanline "somente campo alternado" (`sl_config3[31:30]`) para combinar
  com bob-deint — isolado no bloco SLGEN.
- `[FW]` Verificar bob-deint 480i/576i + telemetria de campo (`interlace_flag`,
  `fid`) no OSD para diagnóstico.

## Abordagem técnica

- Fase 1 (curto): ligar bits existentes — mudança pequena e mensurável.
- Fase 2: interpolação precisa de simulação (criar testbench mínimo para
  scanconverter) ou iteração em HW — sem toolchain local, separar PR.
- Marcar como experimental no menu ("lm deint mode").

## Critérios de aceite

- `lm_deint_mode`/`nir_even_offset` acessíveis e eficazes (verificar em 480i/576i
  reais).
- Nenhum impacto em modo progressivo.

## Referências

- `rtl/scanconverter.v` (~157-158 hooks, ~455-475 bob/NIR),
  `rtl/linebuf_top.v`, `sc_config_regs.h` (~115), issues #100 #132
