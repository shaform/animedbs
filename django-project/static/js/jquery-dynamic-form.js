/**
 * @author Stéphane Roucheray
 * @extends jQuery
 * @version 0.2
 */
(function($){
$.fn.dynamicForm = function (plusElmnt, minusElmnt, options){
	var source = $(this),
	minus = $(minusElmnt),
	plus = $(plusElmnt),
	template = source.clone(true),
	fieldId = 0,
	formFields = "input, checkbox, select, textarea",
	clones = [],
	defaults = {
		duration:1000
  	};
	
  	// Extend default options with those provided
  	options = $.extend(defaults, options);
	
	isPlusDescendentOfTemplate = source.find("*").filter(function(){
		return this == plus.get(0);
	});
	
	isPlusDescendentOfTemplate = isPlusDescendentOfTemplate.length > 0 ? true : false;
	
	function normalizeElmnt(elmnt){
        elmnt.find(formFields).each(function(){
            var nameAttr = $(this).attr("name"), 
			idAttr = $(this).attr("id");

            /* Normalize field name attributes */
            if (!nameAttr) {
				$(this).attr("name", "field" + fieldId);
			}
			
			if (!/\[\]$/.exec(nameAttr)) {
				$(this).attr("name", nameAttr + fieldId);
			}
			
            /* Normalize field id attributes */
            if (idAttr) {
				/* Normalize attached label */
				$("label[for='"+idAttr+"']").each(function(){
					$(this).attr("for", idAttr + fieldId);
				});
				
                $(this).attr("id", idAttr + fieldId);
            }
            fieldId++;
        });
    };
	
	/* Hide minus element */
	minus.hide();
	
	/* If plus element is within the template */
	if (isPlusDescendentOfTemplate) {
		function clickOnPlus(event){
			var clone,
			currentClone = clones[clones.length -1] || source;
			event.preventDefault();
			
			/* On first add, normalize source */
			if (clones.length == 0) {
				normalizeElmnt(source);
				currentClone.find(minusElmnt).hide();
				currentClone.find(plusElmnt).hide();
			}else{
				currentClone.find(plusElmnt).hide();
			}
			
			/* Clone template and normalize it */
			clone = template.clone(true).insertAfter(clones[clones.length - 1] || source);
			normalizeElmnt(clone);
			
			/* Normalize template id attribute */
			if (clone.attr("id")) {
				clone.attr("id", clone.attr("id") + clones.length);
			}
			
			
			plus = clone.find(plusElmnt);
			minus = clone.find(minusElmnt);
			
			minus.get(0).removableClone = clone;
			minus.click(clickOnMinus);
			plus.click(clickOnPlus);
			
			if (options.limit && (options.limit - 2) > clones.length) {
				plus.show();
			}else{
				plus.hide();
			}
			
			clones.push(clone);
		}
		
		function clickOnMinus(event){
			event.preventDefault();
			
			if (this.removableClone.effect && options.removeColor) {
				that = this;
				this.removableClone.effect("highlight", {
					color: options.removeColor
				}, options.duration, function(){that.removableClone.remove();});
			} else {
			
				this.removableClone.remove();
			}
			clones.splice(clones.indexOf(this.removableClone),1);
			if (clones.length == 0){
				source.find(plusElmnt).show();
			}else{
				clones[clones.length -1].find(plusElmnt).show();
			}
		}
		
		/* Handle click on plus */
		plus.click(clickOnPlus);
		
		/* Handle click on minus */
		minus.click(function(event){
			
		});
		
	}else{
	/* If plus element is out of the template */
		/* Handle click on plus */
		plus.click(function(event){
			var clone;
			
			event.preventDefault();
			
			/* On first add, normalize source */
			if (clones.length == 0) {
				normalizeElmnt(source);
				$(minusElmnt).show();
			}
			
			/* Clone template and normalize it */
			clone = template.clone(true).insertAfter(clones[clones.length - 1] || source);
			if (clone.effect && options.createColor) {
				clone.effect("highlight", {color:options.createColor}, options.duration);
			}
			normalizeElmnt(clone);
			
			/* Normalize template id attribute */
			if (clone.attr("id")) {
				clone.attr("id", clone.attr("id") + clones.length);
			}
			if (options.limit && (options.limit - 3) < clones.length) {
				plus.hide();
			}
			clones.push(clone);
		});
		
		/* Handle click on minus */
		minus.click(function(event){
			event.preventDefault();
			var clone = clones.pop();
			if (clones.length >= 0) {
				if (clone.effect && options.removeColor) {
					that = this;
					clone.effect("highlight", {
						color: options.removeColor, mode:"hide"
					}, options.duration, function(){clone.remove();});
				} else {
					clone.remove();
				}
			}
			if (clones.length == 0) {
				$(minusElmnt).hide();
			}
			plus.show();
		});
	}
	
	return source;
};
})(jQuery);
