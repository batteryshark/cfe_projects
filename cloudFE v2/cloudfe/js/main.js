

requirejs.config({
  paths: {
    knockout: "knockout",
    "requirejs-domready": "domReady"
  }
});

require(['knockout', 'containerViewModel', 'placeholderItemFactory', 'requirejs-domready!'], function (ko, ContainerViewModel, ItemFactory, dom) {
    var vm = new ContainerViewModel(new ItemFactory(entry_keys.length));
    ko.applyBindings(vm);

    dom.onkeydown = function(event) {
        switch(event.keyCode)
        {
			case 13: //enter key.
			$("#entry_video").get(0).pause();
			$('#entry_form').submit();
			break;
            case 39: // Right Arrow
				var be = e_db[entry_keys[vm.currentIndex()]];
				$("#entry_video").get(0).pause();
				$("#entry_video").get(0).src = '';
                vm.moveNext();
				$("#selected_id").val(entry_keys[vm.currentIndex()]);
				var ce = e_db[entry_keys[vm.currentIndex()]];
				
				if(ce['year'] != ""){
					$("#name").html(ce['name']+" ("+ce['year']+")");
				}else{
					$("#name").html(ce['name']);
				}
				$("#publisher").html("Publisher: "+ce['publisher']);
				$("#developer").html("Developer: "+ce['developer']);
				$("#region").html("Region: "+ce['region']);
				$("#genre").html("Genre: "+ce['genre']);
				$("#rating").html("Rating: "+ce['rating']);
				$("#players").html("Players: "+ce['players']);
				$("#total_sz").html("Size: "+ce['total_sz']);
				$("#description").html("Description: "+ce['description']);
				$("#entry_video").get(0).src = ce['preview_video'];
				$("#entry_video").get(0).play();
				
                break;
            
            case 37: // Left Arrow
				var be = e_db[entry_keys[vm.currentIndex()]];
				$("#entry_video").get(0).pause();
				$("#entry_video").get(0).src = '';
				
                vm.movePrevious();
				$("#selected_id").val(entry_keys[vm.currentIndex()]);
				var ce = e_db[entry_keys[vm.currentIndex()]];
				
				if(ce['year'] != ""){
					$("#name").html(ce['name']+" ("+ce['year']+")");
				}else{
					$("#name").html(ce['name']);
				}
				$("#publisher").html("Publisher: "+ce['publisher']);
				$("#developer").html("Developer: "+ce['developer']);
				$("#region").html("Region: "+ce['region']);
				$("#genre").html("Genre: "+ce['genre']);
				$("#rating").html("Rating: "+ce['rating']);
				$("#players").html("Players: "+ce['players']);
				$("#total_sz").html("Size: "+ce['total_sz']);
				$("#description").html("Description: "+ce['description']);
				$("#entry_video").get(0).src = ce['preview_video'];
				$("#entry_video").get(0).play();
                break;
        }
    };
});