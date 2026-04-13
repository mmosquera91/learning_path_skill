# 📚 {{topic}}

{{description}}

**Duración estimada:** {{estimated_duration}}

---

## Módulos

{{#modules}}
### {{title}} {{#is_milestone}}🎯{{/is_milestone}}

{{description}}

**Tiempo estimado:** {{estimated_time}}

**Recursos:**
{{#resources}}
- [{{title}}]({{url}}) ({{type}}) {{#verified}}✅{{/verified}}{{^verified}}⚠️{{/verified}}
{{/resources}}
{{^resources}}
- (Sin recursos específicos)
{{/resources}}

---

{{/modules}}

## Próximos pasos

Responde con:
- `/confirm` para activar este plan de aprendizaje
- `/edit <comentarios>` para solicitar cambios
