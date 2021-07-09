

requirejs.config({
  paths: {
    knockout: "knockout",
    "requirejs-domready": "domReady"
  }
});

require(['knockout', 'containerViewModel', 'placeholderItemFactory', 'requirejs-domready!'], function (ko, ContainerViewModel, ItemFactory, dom) {
    var vm = new ContainerViewModel(new ItemFactory(entry_keys.length));
    ko.applyBindings(vm);

	var video = document.getElementById('entry_video');
	video.addEventListener('loadeddata', function() {
   $.get( "get_info?entry_id="+entry_keys[vm.currentIndex()]+"&info_id="+e_db[entry_keys[vm.currentIndex()]]['info_id']+"&cs_name="+cs_name, function( data ) {
		var entry_info = JSON.parse(data);
		//This is where we set our metadata,now.
		if(entry_info['year'] != ""){
					$("#name").html(entry_info['name']+" ("+entry_info['year']+")");
		}else{
					$("#name").html(entry_info['name']);
		}
		
		var ce = e_db[entry_keys[vm.currentIndex()]];
		$("#on_device").html("Installed: "+entry_info['local']);
		$("#publisher").html("Publisher: "+entry_info['publisher']);
		$("#developer").html("Developer: "+entry_info['developer']);
		$("#region").html("Region: "+entry_info['region']);
		$("#genre").html("Genre: "+entry_info['genre']);
		$("#rating").html("Rating: "+entry_info['rating']);
		$("#players").html("Players: "+entry_info['players']);
		$("#total_sz").html("Size: "+ce['size_disp']);
		$("#description").html("Description: "+entry_info['description']);
		$("#loaders_folder_id").val(ce['loaders_folder_id']);
		$("#system_name").val(entry_info['system']);
		$("#pref_loader").val(entry_info['loader']);
				
		});
	}, false);
    dom.onkeydown = function(event) {
		$("#entry_video").get(0).pause();
		$("#entry_video").get(0).src = '';
        switch(event.keyCode)
        {
			case 13: //enter key.
			$('#entry_form').submit();
			break;
            case 39: // Right Arrow
                vm.moveNext();
                break;
            
            case 37: // Left Arrow
                vm.movePrevious();				
                break;
        }
		$("#selected_id").val(entry_keys[vm.currentIndex()]);
		
		
		$("#cs_name").val(e_db[entry_keys[vm.currentIndex()]]['cs_name']);
		
		var ce = e_db[entry_keys[vm.currentIndex()]];
				
		if('preview_video' in ce && ce['preview_video']!=""){
					
		$("#entry_video").get(0).src = ce['preview_video'];
		$("#entry_video").get(0).play();	
		}else{
		$("#entry_video").get(0).src = 'web/image/nopreview.mp4';
		$("#entry_video").get(0).play();
		}
    };
});