

define(['knockout'], function(ko){
    return function(index) {
        this.index = ko.observable(index);
        this.fadingStatus = ko.observable("");
       
		
        this.imageSource = ko.computed(function(){
            var itemLabel = this.index()+1;
            return e_db[entry_keys[index]]["icon_entry"];
			//return "http://placehold.it/200x200&text=" + itemLabel;
        }, this);
    };
});