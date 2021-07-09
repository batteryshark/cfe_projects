	var letter_map = {};
	var current_index = 0;
	function init(){
		for(i=0;i<entry_keys.length;i++){
			var name = e_db[entry_keys[i]]['name'];
			//console.log(e_db[entry_keys[i]]['name']);
			if(!(name[0] in letter_map)){
				letter_map[name[0]] = i;
			}
			
		}
		
	}
	init();
	console.log(letter_map);
	 $(function() {
				
                // and kick off
			
                $('#coverflow').coverflow({
                    select  :   function(event, ui) {
                        console.log("Selected Index: "+ui.index);
                        if(ui.index == 0){
							for(i = 0;i<20;i++){
							$("#preview_"+i).get(0).poster = e_db[entry_keys[i]]['icon'];	
								
							}
						}
						//if(ui.index > 0){
						current_index = ui.index
						
						$("#preview_"+ui.index).get(0).play()
						//}
						
						
						
						
                    },
                    beforeselect: function(event, ui) {
						$("#preview_"+current_index).get(0).pause()
						$("#preview_"+current_index).get(0).src = '';
						$("#preview_"+ui.index).get(0).src=e_db[entry_keys[ui.index]]['preview_video']
						
                        console.log("Flowing to Index: "+ui.index);
						$("#selected_id").val(entry_keys[ui.index]);
						if(e_db[entry_keys[ui.index]]['year'] != ""){
							$("#name").html(e_db[entry_keys[ui.index]]['name']+" ("+e_db[entry_keys[ui.index]]['year']+")");
						}else{
							$("#name").html(e_db[entry_keys[ui.index]]['name']);
							
						}
						$("#publisher").html("Publisher: "+e_db[entry_keys[ui.index]]['publisher']);
						$("#developer").html("Developer: "+e_db[entry_keys[ui.index]]['developer']);
						$("#region").html("Region: "+e_db[entry_keys[ui.index]]['region']);
						$("#genre").html("Genre: "+e_db[entry_keys[ui.index]]['genre']);
						$("#rating").html("Rating: "+e_db[entry_keys[ui.index]]['rating']);
						$("#players").html("Players: "+e_db[entry_keys[ui.index]]['players']);
						$("#total_sz").html("Size: "+e_db[entry_keys[ui.index]]['total_sz']);
						$("#description").html("Description: "+e_db[entry_keys[ui.index]]['description']);
						
	
                        
						
						
                    }
                }
                );
				
			$('#app').keyup(function(event){
				
			if(String.fromCharCode(event.keyCode) in letter_map){
				$('#coverflow' ).coverflow( 'select', letter_map[String.fromCharCode(event.keyCode)] );
			}
	console.log(event.keyCode);
	if(event.keyCode == 39){
	$('#coverflow' ).coverflow( 'select', current_index );
	//$('#coverflow' ).coverflow( 'next' );
	if(current_index > 2 && current_index < entry_keys.length - 2 ){
		$("preview_4").get(0).src = e_db[entry_keys[current_index]]['preview_video'];
		$("preview_4").get(0).poster = e_db[entry_keys[current_index]]['icon'];
		$('#coverflow' ).coverflow( 'select', 3 );
		
	}
	/*
	$('#coverflow').html($('#coverflow').html()+'<video width="640" height="264" >' +
        '<source src="http://video-js.zencoder.com/oceans-clip.mp4" type="video/mp4"></source>' +
        '<source src="http://video-js.zencoder.com/oceans-clip.webm" type="video/webm"></source>' +
        '<source src="http://video-js.zencoder.com/oceans-clip.ogv" type="video/ogg"></source>' +
    '</video>')
	*/
   
	
	}
	
	if(event.keyCode == 40){//down
	
	
	console.log(letter_map[5]);
	

	$('#coverflow' ).coverflow( 'select', offset );
	
	}
	if(event.keyCode == 38){//up
	fletter = e_db[entry_keys[ui.index]]['name'][0];
	nx = String.fromCharCode(fletter.charCodeAt(0) - 1);
	offset = letter_map[nx];
	$('#coverflow' ).coverflow( 'select', offset );
	}
	
	if(event.keyCode == 37){
	$('#coverflow' ).coverflow( 'prev' );
	}
	if(event.keyCode == 13){
	$("#preview_"+current_index).get(0).pause()
	$('#entry_form').submit();
	
	}
	
});
				
            });
