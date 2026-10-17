# Recovery do firmware — OSSC

Kit em `output/`:

| Arquivo | Uso |
|---|---|
| `ossc_1.22-p0fix.bin` | Nossa imagem (bitstream 1.22 stock + firmware com fixes) — update via SD |
| `ossc_1.22-aud.bin` | Imagem oficial 1.22 — reversão via menu/SD |
| `ossc_1.22-aud.jic` | Imagem oficial completa p/ JTAG — recovery de brick |

## Cenário 1: bootou, mas algo está errado

1. Copie `ossc_1.22-aud.bin` para o SD (FAT32).
2. Menu → `Fw. update` → selecione o arquivo → confirme com BTN1.
3. Pronto — volta ao firmware oficial.

Alternativa: `Launch 2nd FW` no menu boota a imagem secundária
(em `0x80000` da flash, gravada pelo `.jic` oficial).

## Cenário 2: não boota (tela preta / sem menu)

Não há fallback automático nem atalho por botão — o soft-core precisa
chegar ao menu para qualquer recovery por software. Caminho é JTAG:

**Necessário:**
- USB Blaster (clone Terasic Blaster funciona)
- Quartus Prime Programmer (parte do Quartus Lite — grátis, conta Intel)
- `output/ossc_1.22-aud.jic`

**Passos:**
1. Ligue o OSSC; conecte o Blaster no conector JTAG da placa e no PC.
2. Abra o Programmer (Quartus → Tools → Programmer).
3. Hardware Setup → selecione o USB-Blaster.
4. Em Tools→Options, marque:
   - "Initiate configuration after programming"
   - "Unprotect EPCS/EPCQ devices selected for Erase/Program operation"
5. Add File → `ossc_1.22-aud.jic` → marque Program/Configure → Start.
6. Ao terminar, o FPGA reconfigura e o firmware oficial sobe.

## Antes de flashar (checklist)

- [ ] `ossc_1.22-aud.bin` também no SD (reversão rápida)
- [ ] Acesso a um USB Blaster disponível, ou aceito o risco
- [ ] `.jic` oficial baixado localmente (já está em `output/`)
