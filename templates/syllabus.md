# 📚 {{topic}}

{{description}}

**Duración estimada:** {{estimated_duration}}

---

## Módulos

{{#modules}}
### {{number}}. {{title}} {{#is_milestone}}🎯{{/is_milestone}}

{{description}}

**Tiempo estimado:** {{estimated_time}}

**Recursos:**
{{#resources}}
- [{{title}}]({{url}}) ({{type}}) {{#verified}}✅{{/verified}}{{^verified}}⚠️{{/verified}}
{{/resources}}

---

{{/modules}}

## Próximos pasos

Responde con:
- `/tutor confirm` para activar este plan de aprendizaje
- `/tutor edit <comentarios>` para solicitar cambios
